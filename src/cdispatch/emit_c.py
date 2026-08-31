"""Emit the C implementation of the entry points.

One C function per command, written as macro invocations, so that a registry
update produces a diff where each new function is one readable block and an
entry point needing something unusual gets a hand-written body sitting inline
beside the generated ones.
"""

from . import ctypes_model as cm
from . import model

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


def is_emittable(command):
    """Whether the C implements everything this command's callers rely on.

    A command the C claimed but implemented only partly would silently drop the
    friendly behaviour its Python wrapper provides.  The generator therefore
    refuses a command rather than emitting a stub that is nearly right.
    """
    if command.helper:
        return False
    if command.return_type.pointers:
        # Only the string returns have a settled conversion so far; the rest --
        # glMapBuffer, the GLsync and platform handle returns -- get
        # hand-written bodies with the Tier 3 families.
        if not (
            command.return_type.pointers == 1
            and command.return_type.base in ('GLubyte', 'GLchar', 'char')
        ):
            return False
    if not command.returns_void and not command.return_type.pointers:
        if cm.scalar_macro(command.return_type) is None:
            return False
    for parameter in command.parameters:
        if isinstance(parameter.size, model.ImageSize):
            return False
        if not parameter.size.declarative:
            return False
        if parameter.is_string_pointer:
            return False
        if parameter.is_output and not isinstance(
            parameter.size, (model.Fixed, model.FromArg, model.GLGetTable)
        ):
            return False
        if not parameter.is_array and parameter.macro is None:
            return False
    if len(command.output_parameters) > 1:
        # Several outputs compose into a tuple return whose ordering is the
        # friendly layer's business; they land with Tier 3.
        return False
    return True


def _return_statement(command, result='_result'):
    """How the stub turns the driver's answer into a Python object."""
    return_type = command.return_type
    if command.returns_void:
        return None
    if return_type.pointers:
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
}


def return_kind(command):
    if command.returns_void:
        return RETURN_KINDS['void']
    if command.return_type.pointers:
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
    arrays = [p for p in command.parameters if p.is_array]
    outputs = command.output_parameters
    required = len(command.required_arguments)
    total = len(command.parameters)

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
        if parameter.is_array:
            continue
        lines.append(
            '    %s(%d, %s);' % (_scalar_macro(parameter), index, parameter.c_name)
        )
    lines.append('    PYGL_CONV_OK();')

    for index, parameter in enumerate(command.parameters):
        if not parameter.is_array:
            continue
        element = element_symbol(parameter)
        if parameter.is_output and isinstance(parameter.size, model.GLGetTable):
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
    if command.returns_void:
        lines.append(
            '    PYGL_CALL_V((%s), (%s));' % (signature or 'void', arguments)
        )
    else:
        lines.append(
            '    PYGL_CALL_R(_result, %s, (%s), (%s));'
            % (cm.abi_c_type(command.return_type), signature or 'void', arguments)
        )
    lines.append('    PYGL_CHECK();')

    if outputs:
        output = outputs[0]
        if isinstance(output.size, model.GLGetTable):
            # The count is not known until the table has been consulted.
            size = '%s_count' % (output.c_name,)
        else:
            size = '(Py_ssize_t)(%s)' % (_size_expression(command, output),)
        lines.append(
            '    PyObject *_value = pygl_output_value(&_bufs[%s_slot], %s, %s);'
            % (output.c_name, element_symbol(output), size)
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
    lines = []
    if command.parameters:
        lines.append(
            'static const char *const %s_args[] = {%s};'
            % (symbol, ', '.join(_c_string(p.name) for p in command.parameters))
        )
        args = '%s_args' % (symbol,)
    else:
        args = 'NULL'
    doc = command.signature_line()
    if command.purpose:
        doc = '%s\n\n%s' % (doc, command.purpose)
    lines.append(
        'static const PyGLCommand %s_info = '
        '{%s, %s, %s, %s, %s, %d, %d, %s, %d, %d, %d};'
        % (
            symbol,
            _c_string(command.name),
            _c_string(doc),
            _c_string(command.text_signature()),
            args,
            _c_string(command.feature),
            len(command.parameters),
            slot,
            _API_ENUM[command.api],
            1 if command.deprecated else 0,
            len(command.required_arguments),
            return_kind(command),
        )
    )
    return '\n'.join(lines) + '\n'


def emit_translation_unit(api, commands, slots):
    """One ``.c`` file holding every emitted stub for one API."""
    parts = [
        '/* Generated by src/cdispatch -- do not edit.',
        ' *',
        ' * The %s entry points, one C function each.  See plans/C-DISPATCH.md.' % (api,),
        ' */',
        '#include "pygl.h"',
        '#include "pygl_elements.h"',
        '#include "pygl_glgets.h"',
        '',
    ]
    for command in commands:
        parts.append(emit_command_record(command, slots[(command.api, command.name)]))
        parts.append(emit_stub(command))
        parts.append('')
    parts.append(
        'const PyGLEntry pygl_entries_%s[] = {' % (api,)
    )
    for command in commands:
        symbol = stub_symbol(command)
        parts.append(
            '    {&%s_info, (vectorcallfunc)%s},' % (symbol, symbol)
        )
    parts.append('    {NULL, NULL}')
    parts.append('};')
    parts.append('')
    return '\n'.join(parts)
