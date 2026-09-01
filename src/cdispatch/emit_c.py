"""Emit the C implementation of the entry points.

One C function per command, written as macro invocations, so that a registry
update produces a diff where each new function is one readable block and an
entry point needing something unusual gets a hand-written body sitting inline
beside the generated ones.
"""

from . import blocking
from . import ctypes_model as cm
from . import handwritten, model

__all__ = [
    'emit_stub',
    'is_emittable',
    'emit_translation_unit',
    'element_symbol',
    'element_name',
]

#: Macro name per scalar converter class.
_MACRO = {
    'GL_U': 'PYGL_U',
    'GL_I': 'PYGL_I',
    'GL_B': 'PYGL_B',
    'GL_F': 'PYGL_F',
    'GL_D': 'PYGL_D',
    'GL_I64': 'PYGL_I64',
    'GL_U64': 'PYGL_U64',
    'GL_IPTR': 'PYGL_IPTR',
    'GL_OPAQUE': 'PYGL_OPAQUE',
    'GL_HANDLE': 'PYGL_HANDLE',
}

#: ``GLsizei`` reads through the same macro as ``GLint`` but is spelled
#: distinctly in the generated source, because that is what the plan's example
#: shows and because it makes a signed-size argument recognisable in a diff.
_SIZE_BASES = frozenset(['GLsizei'])


def element_name(base):
    """A C identifier for an element type.

    Registry base types include ``unsigned int`` and ``char``, which are not
    identifiers, so the symbol is sanitised rather than interpolated raw.
    """
    return ''.join(character if character.isalnum() else '_' for character in base)


def element_symbol(parameter):
    """The static element description a stub names for an array parameter."""
    ctype = parameter.ctype
    if ctype.base == 'void' and ctype.pointers == 1 and parameter.is_output:
        # wrapper.setOutput resolves a void * output to GLubyteArray, so an
        # output array of the wrong type is coerced -- which is what tells the
        # caller their result would not have reached them.
        return '&pygl_elem_GLubyte'
    if ctype.pointers > 1:
        # An array of pointers.  GLvoidpArray is what setOutput derives from
        # the ctypes argtype, and it is the only array class that can size an
        # allocation of them.
        return '&pygl_elem_voidp'
    if ctype.base == 'void':
        return '&pygl_elem_any'
    element = cm.element_type(ctype.base)
    if not element.buffer_format:
        return '&pygl_elem_any'
    return '&pygl_elem_%s' % (element_name(ctype.base),)


def _scalar_macro(parameter):
    macro = _MACRO[parameter.macro]
    if parameter.ctype.base in _SIZE_BASES:
        macro = 'PYGL_SZ'
    return macro


def _output_size(command, parameter):
    """The element count an output contributes to the return value."""
    if isinstance(parameter.size, model.ImageSize):
        return '0'
    if isinstance(parameter.size, model.GLGetTable):
        # Not known until the pname table has been consulted at run time.
        return '%s_count' % (parameter.c_name,)
    return '(Py_ssize_t)(%s)' % (_size_expression(command, parameter),)


def _size_expression(command, parameter):
    """The element count for a sized parameter, as a C expression."""
    size = parameter.size
    if isinstance(size, model.Fixed):
        return str(size.count)
    if isinstance(size, model.FromArg):
        source = command.parameters[size.argument].c_name
        if size.divisor == 1:
            return source
        return '%s / %d' % (source, size.divisor)
    raise ValueError('no C expression for %r' % (size,))


def _outputs_are_trailing(command):
    """Whether every output is at the end of the argument list.

    An output is optional -- the caller may pass their own array or leave it to
    be allocated -- and that is only expressible positionally when the outputs
    trail.  An output in the middle has no arity at which omitting it is
    unambiguous, because the next argument would shift into its place.
    """
    positions = [
        index
        for index, parameter in enumerate(command.parameters)
        if parameter.is_output
    ]
    if not positions:
        return True
    total = len(command.parameters)
    return positions == list(range(total - len(positions), total))


def hand_written(command):
    """The hand-written implementation for this command, or None."""
    return handwritten.lookup(command.api, command.name)


def implements_friendly(command):
    """Whether the C does everything the Python wrapper would have done.

    The friendly modules restate each entry point's behaviour as a chain of
    customisation calls.  Where the C already performs what the call
    describes, the call must be a no-op returning the entry point -- otherwise
    it falls back to the ctypes wrapper and the work is undone.
    """
    if hand_written(command) is not None:
        return True
    if command.retains:
        return True
    return any(
        isinstance(parameter.size, (model.ImageSize, model.TypedArray))
        for parameter in command.parameters
    )


def exclusion_reason(command):
    """Why the C does not implement this command, or '' when it does.

    Every command left on the ctypes path has a reason here, so that
    ``src/check_registry.py`` can account for all of them and nothing is left
    behind silently.
    """
    if command.name in handwritten.EXCLUDED:
        return 'built in place by the Python layer'
    if hand_written(command) is not None:
        return ''
    if command.helper and command.helper != 'variadic':
        return 'hand-written family: %s' % (command.helper,)
    if command.return_type.pointers and not (
        command.return_type.pointers == 1
        and command.return_type.base in ('GLubyte', 'GLchar', 'char', 'void')
    ):
        return 'pointer return: %s' % (command.return_type.declaration(),)
    if (
        not command.returns_void
        and not command.return_type.pointers
        and cm.scalar_macro(command.return_type) is None
    ):
        return 'unknown return type: %s' % (command.return_type.base,)
    for parameter in command.parameters:
        if parameter.is_string_pointer:
            continue
        if isinstance(parameter.size, (model.ImageSize, model.TypedArray)):
            continue
        if not parameter.size.declarative:
            return 'non-declarative size'
        if parameter.is_output and not isinstance(
            parameter.size, (model.Fixed, model.FromArg, model.GLGetTable, model.ImageSize)
        ):
            return 'output with no expressible size'
        if not parameter.is_array and parameter.macro is None:
            return 'unknown parameter type: %s' % (parameter.ctype.base,)
    if not _outputs_are_trailing(command):
        return 'outputs are not the trailing arguments'
    return ''


def is_emittable(command):
    """Whether the C implements everything this command's callers rely on.

    A command the C claimed but implemented only partly would silently drop the
    friendly behaviour its Python wrapper provides.  The generator therefore
    refuses a command rather than emitting a stub that is nearly right.
    """
    if command.name in handwritten.EXCLUDED:
        return False
    if hand_written(command) is not None:
        return True
    if command.helper and command.helper != 'variadic':
        # A convenience signature on top is the Python layer's business; the
        # entry point underneath is ordinary, and the marshalling belongs
        # here either way.
        return False
    if command.return_type.pointers:
        # Only the string returns have a settled conversion so far; the rest --
        # glMapBuffer, the GLsync and platform handle returns -- get
        # hand-written bodies with the Tier 3 families.
        if not (
            command.return_type.pointers == 1
            and command.return_type.base in ('GLubyte', 'GLchar', 'char', 'void')
        ):
            return False
    if not command.returns_void and not command.return_type.pointers:
        if cm.scalar_macro(command.return_type) is None:
            return False
    for parameter in command.parameters:
        if parameter.is_string_pointer:
            continue
        if isinstance(parameter.size, (model.ImageSize, model.TypedArray)):
            continue
        if not parameter.size.declarative:
            return False
        if parameter.is_output and not isinstance(
            parameter.size, (model.Fixed, model.FromArg, model.GLGetTable)
        ):
            return False
        if not parameter.is_array and parameter.macro is None:
            return False
    return _outputs_are_trailing(command)


def _return_statement(command, result='_result'):
    """How the stub turns the driver's answer into a Python object."""
    return_type = command.return_type
    if command.returns_void:
        return None
    if return_type.pointers:
        if return_type.base == 'void':
            # glMapBuffer and its relatives hand back the address itself, as
            # an int, or None for a null pointer.  It is a mapped region, not
            # a string, so there is nothing to copy out of it.
            return 'pygl_address_or_none(%s)' % (result,)
        return 'pygl_bytes_or_none((const char *)%s)' % (result,)
    macro = cm.scalar_macro(return_type)
    if macro in ('GL_U64',):
        return 'PyLong_FromUnsignedLongLong((unsigned long long)%s)' % (result,)
    if macro == 'GL_I64':
        return 'PyLong_FromLongLong((long long)%s)' % (result,)
    if macro == 'GL_IPTR':
        return 'PyLong_FromSsize_t((Py_ssize_t)%s)' % (result,)
    if macro == 'GL_OPAQUE':
        return 'pygl_opaque((void *)%s, "%s")' % (result, return_type.base)
    if macro == 'GL_U':
        return 'PyLong_FromUnsignedLong((unsigned long)%s)' % (result,)
    if macro in ('GL_F', 'GL_D'):
        return 'PyFloat_FromDouble((double)%s)' % (result,)
    # GLboolean returns stay int, not bool: glIsTexture returns 0 today and
    # will return 0.  Changing it is a separate, deliberate API decision.
    return 'PyLong_FromLong((long)%s)' % (result,)


#: Which conversion the stub applies to the driver's answer.  Mirrors the
#: PYGL_RET_* enum in pygl.h, and lets an assignment to restype that asks for
#: the conversion already in place be accepted rather than demote the function.
RETURN_KINDS = {
    'void': 0,
    'int': 1,
    'bytes': 2,
    'float': 3,
    'opaque': 4,
    'address': 5,
}


def return_kind(command):
    if command.returns_void:
        return RETURN_KINDS['void']
    if command.return_type.pointers:
        if command.return_type.base == 'void':
            return RETURN_KINDS['address']
        return RETURN_KINDS['bytes']
    macro = cm.scalar_macro(command.return_type)
    if macro in ('GL_F', 'GL_D'):
        return RETURN_KINDS['float']
    if macro == 'GL_OPAQUE':
        return RETURN_KINDS['opaque']
    return RETURN_KINDS['int']


def stub_symbol(command):
    return 'pygl_%s_%s' % (command.api, command.name)


def emit_stub(command):
    """The C function implementing one entry point."""
    lines = []
    arrays = [p for p in command.parameters if p.is_array or p.is_string_pointer]
    outputs = command.output_parameters
    required = len(command.required_arguments)
    total = len(command.parameters)

    # Array parameters take frame slots in declaration order, so a slot index
    # is a compile-time constant the generator can name directly.
    frame_slots = {
        parameter.name: slot
        for slot, parameter in enumerate(
            p for p in command.parameters if p.is_array or p.is_string_pointer
        )
    }

    lines.append('static PyObject *')
    lines.append(
        '%s(GLProc *self, PyObject *const *_a, size_t _nargsf)'
        % (stub_symbol(command),)
    )
    lines.append('{')
    if outputs:
        lines.append('    PYGL_ARITY_RANGE(%d, %d);' % (required, total))
    else:
        lines.append('    PYGL_ARITY(%d);' % (total,))
    if arrays:
        lines.append('    PYGL_FRAME(%d);' % (len(arrays),))

    for index, parameter in enumerate(command.parameters):
        if parameter.is_array or parameter.is_string_pointer:
            continue
        lines.append(
            '    %s(%d, %s);' % (_scalar_macro(parameter), index, parameter.c_name)
        )
    lines.append('    PYGL_CONV_OK();')

    for index, parameter in enumerate(command.parameters):
        if not (parameter.is_array or parameter.is_string_pointer):
            continue
        element = element_symbol(parameter)
        if parameter.is_string_pointer:
            lines.append(
                '    PYGL_STRING_ARRAY(%d, %s);' % (index, parameter.c_name)
            )
        elif isinstance(parameter.size, model.TypedArray):
            lines.append(
                '    PYGL_ARRAY_TYPED(%d, %s, %s, %d);'
                % (
                    index,
                    parameter.c_name,
                    command.parameters[parameter.size.type_argument].c_name
                    if parameter.size.type_argument >= 0
                    else '0',
                    1 if parameter.retain else 0,
                )
            )
        elif isinstance(parameter.size, model.ImageSize):
            size = parameter.size
            dimensions = [
                command.parameters[index].c_name for index in size.dimensions
            ]
            dimensions += ['0'] * (3 - len(dimensions))
            lines.append(
                '    PYGL_IMAGE_%s(%d, %s, %s, %s, %d, %s);'
                % (
                    'OUT' if parameter.is_output else 'IN',
                    index,
                    parameter.c_name,
                    command.parameters[size.format_argument].c_name,
                    command.parameters[size.type_argument].c_name,
                    len(size.dimensions),
                    ', '.join(dimensions),
                )
            )
        elif parameter.is_output and isinstance(parameter.size, model.GLGetTable):
            pname = command.parameters[parameter.size.pname_argument].c_name
            lines.append(
                '    PYGL_ARRAY_OUT_GLGET(%d, %s, %s, %s, pygl_glget_%s);'
                % (index, parameter.c_name, element, pname, command.api)
            )
        elif parameter.is_output:
            lines.append(
                '    PYGL_ARRAY_OUT(%d, %s, %s, (Py_ssize_t)(%s));'
                % (index, parameter.c_name, element, _size_expression(command, parameter))
            )
        elif isinstance(parameter.size, model.Fixed):
            lines.append(
                '    PYGL_ARRAY_IN_SIZED(%d, %s, %s, %d);'
                % (index, parameter.c_name, element, parameter.size.count)
            )
        else:
            lines.append(
                '    PYGL_ARRAY_IN(%d, %s, %s);'
                % (index, parameter.c_name, element)
            )

    signature = ', '.join(
        cm.abi_c_type(parameter.ctype) for parameter in command.parameters
    )
    arguments = ', '.join(parameter.c_name for parameter in command.parameters)
    # A call that can wait releases the GIL for the duration.  See
    # src/cdispatch/blocking.py for which, and why it is not all of them.
    waits = '_BLOCKING' if blocking.blocks(command.name) else ''
    if command.returns_void:
        lines.append(
            '    PYGL_CALL_V%s((%s), (%s));' % (waits, signature or 'void', arguments)
        )
    else:
        lines.append(
            '    PYGL_CALL_R%s(_result, %s, (%s), (%s));'
            % (
                waits,
                cm.abi_c_type(command.return_type),
                signature or 'void',
                arguments,
            )
        )
    lines.append('    PYGL_CHECK();')

    for index, parameter in enumerate(command.parameters):
        if parameter.retain:
            lines.append(
                '    if (pygl_retain(self, %d, &_bufs[%d]) < 0) goto _fail;'
                % (index, frame_slots[parameter.name])
            )

    retained = [p for p in command.parameters if p.retain]
    if retained and command.returns_void and not outputs:
        # The friendly form hands back the converted array, which is what a
        # caller keeps in order to change the data it is drawing from.
        lines.append(
            '    PyObject *_value = pygl_retained_value(&_bufs[%d]);'
            % (frame_slots[retained[0].name],)
        )
        lines.append('    PYGL_CLEANUP();')
        lines.append('    return _value;')
    elif len(outputs) > 1:
        # A local rather than a static: a glGet-sized output's count is not
        # known until the table has been consulted.
        lines.append('    const PyGLOutput _outputs[] = {')
        for output in outputs:
            lines.append(
                '        {%d, %s, %s},'
                % (
                    frame_slots[output.name],
                    element_symbol(output),
                    _output_size(command, output),
                )
            )
        lines.append('    };')
        lines.append(
            '    PyObject *_value = pygl_output_tuple(_bufs, _outputs, %d);'
            % (len(outputs),)
        )
        lines.append('    PYGL_CLEANUP();')
        lines.append('    return _value;')
    elif outputs and isinstance(outputs[0].size, model.ImageSize):
        output = outputs[0]
        lines.append(
            '    PyObject *_value = pygl_image_value(&_bufs[%s_slot], %s);'
            % (output.c_name, command.parameters[outputs[0].size.type_argument].c_name)
        )
        lines.append('    PYGL_CLEANUP();')
        lines.append('    return _value;')
    elif outputs:
        output = outputs[0]
        lines.append(
            '    PyObject *_value = pygl_output_value(&_bufs[%s_slot], %s, %s);'
            % (output.c_name, element_symbol(output), _output_size(command, output))
        )
        lines.append('    PYGL_CLEANUP();')
        lines.append('    return _value;')
    elif command.returns_void:
        if arrays:
            lines.append('    PYGL_CLEANUP();')
        lines.append('    Py_RETURN_NONE;')
    else:
        statement = _return_statement(command)
        if arrays:
            lines.append('    PyObject *_value = %s;' % (statement,))
            lines.append('    PYGL_CLEANUP();')
            lines.append('    return _value;')
        else:
            lines.append('    return %s;' % (statement,))

    lines.append('_fail:')
    if arrays:
        lines.append('    PYGL_CLEANUP();')
    lines.append('    return NULL;')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def _c_string(value):
    if value is None:
        return 'NULL'
    escaped = (
        value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    )
    return '"%s"' % (escaped,)


_API_ENUM = {
    'GL': 'PYGL_API_GL',
    'GLES1': 'PYGL_API_GLES1',
    'GLES2': 'PYGL_API_GLES2',
    'GLES3': 'PYGL_API_GLES3',
    'GLSC2': 'PYGL_API_GLSC2',
    'GLX': 'PYGL_API_GLX',
    'WGL': 'PYGL_API_WGL',
    'EGL': 'PYGL_API_EGL',
}


def emit_command_record(command, slot):
    """The static metadata a GLProc exposes to Python."""
    symbol = stub_symbol(command)
    hand = hand_written(command)
    # argNames reports the C entry point's argument names even where the
    # friendly form takes fewer, because that is what it reports today.
    arg_names = (
        list(hand.c_arg_names)
        if hand is not None and hand.c_arg_names
        else [p.name for p in command.parameters]
    )
    #: What the docstring and the text signature describe.
    call_names = list(hand.arg_names) if hand else arg_names
    lines = []
    if arg_names:
        lines.append(
            'static const char *const %s_args[] = {%s};'
            % (symbol, ', '.join(_c_string(name) for name in arg_names))
        )
        args = '%s_args' % (symbol,)
    else:
        args = 'NULL'
    doc = hand.signature if hand else command.signature_line()
    if command.purpose:
        doc = '%s\n\n%s' % (doc, command.purpose)
    lines.append(
        'static const PyGLCommand %s_info = '
        '{%s, %s, %s, %s, %s, %s, %d, %d, %s, %d, %d, %d, %d};'
        % (
            symbol,
            _c_string(command.name),
            _c_string(doc),
            _c_string(
            '($module, %s, /)' % (', '.join(call_names),)
            if hand
            else command.text_signature()
        ),
            args,
            _c_string(command.feature),
            # The other extensions that declare it.  A driver advertising any
            # of them has the function, so resolution tries them all.
            _c_string(
                ','.join(
                    name for name in command.extensions if name != command.feature
                )
            ),
            len(arg_names),
            slot,
            _API_ENUM[command.api],
            1 if command.deprecated else 0,
            len(call_names),
            return_kind(command),
            1 if implements_friendly(command) else 0,
        )
    )
    return '\n'.join(lines) + '\n'


def emit_translation_unit(api, commands, slots, provenance=''):
    """One ``.c`` file holding every emitted stub for one API."""
    parts = [
        provenance
        or '/* Generated by src/cdispatch -- do not edit. */',
        '',
        '/* The %s entry points, one C function each.  See plans/C-DISPATCH.md. */'
        % (api,),
        '#include "pygl.h"',
        '#include "pygl_elements.h"',
        '#include "pygl_glgets.h"',
        '',
    ]
    declared = set()
    for command in commands:
        hand = hand_written(command)
        parts.append(emit_command_record(command, slots[(command.api, command.name)]))
        if hand is not None:
            if hand.symbol not in declared:
                parts.append(
                    'PyObject *%s(GLProc *self, PyObject *const *_a, '
                    'size_t _nargsf);' % (hand.symbol,)
                )
                declared.add(hand.symbol)
        else:
            parts.append(emit_stub(command))
        parts.append('')
    parts.append(
        'const PyGLEntry pygl_entries_%s[] = {' % (api,)
    )
    for command in commands:
        hand = hand_written(command)
        symbol = stub_symbol(command)
        parts.append(
            '    {&%s_info, (vectorcallfunc)%s},'
            % (symbol, hand.symbol if hand else symbol)
        )
    parts.append('    {NULL, NULL}')
    parts.append('};')
    parts.append('')
    return '\n'.join(parts)
