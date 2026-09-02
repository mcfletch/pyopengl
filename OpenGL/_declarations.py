"""What the generated ``OpenGL.raw`` modules used to declare.

Every one of them held the same three things -- an extension name, a set of
constants, and a set of entry-point declarations -- and nothing else.  A
friendly module took them all with ``from OpenGL.raw.GL.VERSION.GL_1_1 import
*``, which meant building a module object and a dictionary in order to copy
that dictionary into another one.

:func:`define` writes them into the friendly module's own namespace instead, so
there is one dictionary rather than two and no module in between.

Two sources hold the same facts, and which one answers depends only on what was
built:

* the C dispatch extension, where the declarations sit in ``.rodata`` and cost
  nothing until asked for;
* ``OpenGL/raw/_declarations/<API>.dat``, written by the generator in the same
  pass, for an installation with no compiled extension.

They are generated together from the registry and the shipped tree, so they
cannot drift.  ``python src/regenerate_c.py`` writes both.
"""

import importlib
import os

__all__ = ['define', 'contents_for', 'clear_caches']

#: Where the marshalled declarations live, relative to this file.
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', '_declarations')

#: One entry per API, filled on the first module of that API that asks.
_data = {}

#: The customisations, read from the shipped table on first use.  What a
#: friendly module used to apply as a chain of wrapper.wrapper(...) calls.
_annotations = None

#: Resolved type expressions, keyed by ``(api, text)``.  The vocabulary is
#: small and the uses are not: ``_cs.GLenum`` is written thousands of times
#: across the tree, and evaluating it thousands of times was the largest single
#: cost of importing without the C extension.
_types_cache = {}

#: The C extension, once, or False when there is none to use.
_extension = None

#: The namespace each generated module declares, built on the first friendly
#: module that asks and copied from thereafter.  GL_1_1 re-exports GL_1_0,
#: GL_1_2 re-exports GL_1_1, and forty friendly modules stand on the chain; a
#: module object used to be what stopped that from being rebuilt every time,
#: and this is what stops it now.
_namespaces = {}


def _c_source():
    """The dispatch extension, if it is the implementation in use."""
    global _extension
    if _extension is None:
        from OpenGL import _configflags

        _extension = False
        if _configflags.DISPATCH == 'c':
            try:
                from OpenGL import _dispatch
            except ImportError:
                pass
            else:
                # Installing is what fills `entry_points`, and nothing else
                # does it now: it used to happen on the first createFunction
                # call, and no generated declaration runs any more.
                if _dispatch.install():
                    _extension = _dispatch._c
    return _extension


def _data_source(api):
    """The shipped declarations for one API, read once."""
    if api not in _data:
        import marshal

        path = os.path.join(DATA, '%s.dat' % (api,))
        try:
            with open(path, 'rb') as handle:
                _data[api] = marshal.load(handle)
        except OSError:
            _data[api] = {}
    return _data[api]


def api_of(module_name):
    """``OpenGL.raw.GL.VERSION.GL_1_1`` names the GL API."""
    parts = module_name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


def contents_for(module_name):
    """What one generated module declared, or None if nothing describes it.

    A mapping with ``extension``, ``constants``, ``commands`` and ``reexports``
    -- the same shape from either source, so nothing above here has to know
    which one answered.
    """
    extension = _c_source()
    if extension:
        # The two sources are generated together and describe the same set, so
        # one that does not know a module says the module is not generated --
        # reading the other to be told so again would mean loading half a
        # megabyte to learn nothing.
        return extension.module_contents(module_name)
    blob = _data_source(api_of(module_name)).get(module_name)
    if blob is None:
        return None
    import marshal

    name, constants, commands, reexports = marshal.loads(blob)
    return {
        'extension': name,
        'constants': constants,
        'commands': commands,
        'reexports': reexports,
    }


def annotations():
    """The customisation table, or an empty one where it was not shipped."""
    global _annotations
    if _annotations is None:
        import marshal

        try:
            with open(os.path.join(DATA, '_annotations.dat'), 'rb') as handle:
                _annotations = marshal.load(handle)
        except OSError:
            _annotations = {}
    return _annotations


def customise_entry(entry, api, name, declared):
    """Apply what the table says about this entry point, and return it.

    The rule:

    * a parameter takes an array conversion when the table says ``array``;
    * the length comes from the table where there is one, and there usually is
      not -- ``setInputArraySize(x, None)`` states a conversion and no length.

    The table says it rather than the declared type saying it, because the type
    cannot: ``glDrawElements`` and relatives declare their array
    ``ctypes.c_void_p``, since it may be a client pointer or a buffer offset.
    Reading array-ness off the type instead both loses those and invents
    conversions for parameters the friendly layer never wrapped, which is 171
    entry points' worth of difference from what the modules did.

    An **output** parameter is rebuilt from the same table.  What ``setOutput``
    needs beyond a size is the argument whose value sizes it and whether a
    caller may pass the array in instead; the table holds the first and the
    second is ``True`` for every one of the 688 calls in the tree, so it is not
    recorded per entry.  Three of the four size kinds are expressed here --
    a fixed count, a count read from another argument, and the ``_glgets``
    table.  An **image** size is not: it is computed from the format and type
    arguments together, and the modules that need one keep their own chain.

    A ``GLProc`` is returned untouched: the C already performs all of this,
    which is what ``implements_friendly`` records.
    """
    entry_annotations = annotations().get('%s.%s' % (api, name))
    parameters = (entry_annotations or {}).get('parameters', {})
    if not parameters and not declared:
        return entry
    from OpenGL import wrapper

    outputs = _output_parameters(parameters)
    if outputs is None:
        # A size this rule cannot state.  Rebuilding the inputs and leaving the
        # outputs would be worse than leaving the module its chain, because the
        # result would be a wrapper that looks complete and is not.
        return entry

    built = entry
    for parameter, _kind in declared:
        bits = parameters.get(parameter, {})
        if bits.get('out'):
            continue          # rebuilt below, in the order the chain used
        if not bits.get('array'):
            continue
        size = bits.get('size')
        if size is not None and size.get('kind') == 'fixed':
            length = size['count']
        else:
            length = None
        if built is entry:
            built = wrapper.wrapper(entry)
        built = built.setInputArraySize(parameter, length)

    for _order, parameter, size in outputs:
        if built is entry:
            built = wrapper.wrapper(entry)
        kind = size['kind']
        if kind == 'fixed':
            built = built.setOutput(
                parameter, size=(size['count'],), orPassIn=True
            )
        elif kind == 'from-argument':
            built = built.setOutput(
                parameter,
                size=_scaled_by(size.get('divisor', 1)),
                pnameArg=size['argument'],
                orPassIn=True,
            )
        else:
            glgets = _import('OpenGL.raw.%s._glgets' % (api,))
            built = built.setOutput(
                parameter,
                size=glgets._glget_size_mapping,
                pnameArg=size['pname'],
                orPassIn=True,
            )
    return built


#: The size kinds the rule states.  ``image`` is absent deliberately: an image
#: size comes from the format and type arguments together rather than from one
#: value, and the modules that need one keep their chain.
_OUTPUT_SIZE_KINDS = frozenset(['fixed', 'from-argument', 'glget-table'])


def _output_parameters(parameters):
    """``[(order, name, size), ...]``, or ``None`` if one cannot be stated.

    The order is the one the chain applied them in, which the table records
    because ``setOutput`` builds the Python signature and the signature is
    ordered.
    """
    outputs = []
    for parameter, bits in parameters.items():
        if not bits.get('out'):
            continue
        size = bits.get('size')
        if size is None or size.get('kind') not in _OUTPUT_SIZE_KINDS:
            return None
        outputs.append((bits.get('output_order', 0), parameter, size))
    outputs.sort(key=lambda item: item[0])
    return outputs


def _scaled_by(divisor):
    """``setOutput``'s size function: the named argument's value, over N."""
    if divisor == 1:
        return lambda value: (value,)
    return lambda value: (value // divisor,)


def _import(name):
    import importlib

    return importlib.import_module(name)


def define(namespace, module_name, customise=False):
    """Define, in ``namespace``, everything ``module_name`` declared.

    ``customise`` says that the friendly module has handed its customisation
    chain over to the annotation table and no longer applies it itself.  It is
    per module because applying a customisation twice is an error, not a
    no-op -- ``wrapper`` raises ``Double wrapping of output parameter`` -- so
    the modules can only be migrated one at a time if each says whether it has
    been.  When they all have, the flag goes.

    Called from a friendly module in place of the ``import *`` that used to
    reach the generated module::

        _EXTENSION_NAME = define(globals(), 'OpenGL.raw.GL.VERSION.GL_1_1')

    Returns the extension name, because the caller wants it under
    ``_EXTENSION_NAME`` and it is the one thing the module says about itself.
    """
    built, extension = _build(module_name)
    namespace.update(built)
    if customise:
        api = api_of(module_name)
        contents = contents_for(module_name) or {}
        for command, arguments, types in contents.get('commands', ()):
            entry = namespace.get(command)
            if entry is None:
                continue
            replacement = customise_entry(
                entry, api, command, _array_parameters(arguments, types)
            )
            if replacement is not entry:
                namespace[command] = replacement
    return extension


def _array_parameters(arguments, types):
    """``[(name, 'array' | 'scalar'), ...]`` from the declaration's text.

    Array-ness is half the rebuild rule, and the half the table does not hold:
    it is a property of the type the declaration stated.  Read from the text
    rather than from the built binding, because on a C entry point reading
    ``argtypes`` builds the ctypes binding the import path exists to avoid --
    which is what made this cost 1,143 bindings the first time it was written.
    """
    if isinstance(arguments, str):
        arguments = [name for name in arguments.split(',') if name]
    if isinstance(types, str):
        types = types.split(',')
    # types is the result type followed by one per parameter.
    parameter_types = list(types)[1:]
    if len(parameter_types) != len(arguments):
        return ()
    return tuple(
        (name, 'array' if text.startswith('arrays.') else 'scalar')
        for name, text in zip(arguments, parameter_types)
    )


def _build(module_name):
    """The names one generated module declares, and its extension name.

    Built once and handed out by reference after that, which is what a module
    object used to do for this.
    """
    remembered = _namespaces.get(module_name)
    if remembered is not None:
        return remembered

    contents = contents_for(module_name)
    if contents is None:
        # Nothing describes it: the module is one of the hand-written few, or
        # this is a checkout with neither the extension nor the data.  Importing
        # it is what used to happen and still works.
        module = importlib.import_module(module_name)
        exported = getattr(module, '__all__', None)
        if exported is None:
            # What ``import *`` would have taken: a private name is the
            # module's own working material, not something it defines.
            exported = [key for key in vars(module) if not key.startswith('_')]
        built = {key: getattr(module, key) for key in exported}
        result = (built, getattr(module, '_EXTENSION_NAME', ''))
        _namespaces[module_name] = result
        return result

    built = {}
    # A module built on another one re-exported it, and a caller of the
    # friendly module expects those names too.
    for source in contents['reexports']:
        built.update(_build(source)[0])

    from OpenGL.constant import Constant

    for key, value in contents['constants'].items():
        built[key] = Constant(key, value)

    api = api_of(module_name)
    extension = contents['extension']
    for command, arguments, types in contents['commands']:
        built[command] = entry_point(
            api, command, extension, module_name, arguments, types
        )
    result = (built, extension)
    _namespaces[module_name] = result
    return result


def entry_point(api, name, extension, module_name, arguments, types):
    """The callable a client gets for one entry point.

    The C implementation where there is one, and the ctypes binding otherwise.
    Either way the declaration is remembered rather than built, because what
    builds a ctypes binding is only wanted where a client demotes -- which
    happens for a few dozen entry points out of nearly five thousand.
    """
    from OpenGL._dispatch import entry_points, support

    proc = entry_points.get((api, name))
    if proc is None:
        # No C entry point, so the ctypes binding is the entry point rather
        # than something to fall back to: build it, and do not also record how
        # to build it.
        return Declaration(api, name, extension, module_name, arguments, types)()
    # Where the C implements it, what the binding is for is demotion and the
    # argtypes/restype/DLL attributes.  Few callers ever ask, so the
    # declaration is remembered and the binding built if one does.
    support.register_ctypes_factory(
        api, name, Declaration(api, name, extension, module_name, arguments, types)
    )
    support.register_module(api, name, module_name)
    return proc


class Declaration:
    """What a generated module's ``@_p.types(...) def glFoo(...)`` said.

    Held as the text it was written in and turned into a ctypes binding on the
    first call that asks for one, because most entry points never see one.
    """

    __slots__ = ('_arguments', '_types', 'api', 'extension', 'module', 'name')

    def __init__(self, api, name, extension, module, arguments, types):
        self.api = api
        self.name = name
        self.extension = extension
        self.module = module
        self._arguments = arguments
        self._types = types

    def _resolve_types(self):
        """``('None', '_cs.GLenum', 'arrays.GLfloatArray')`` as the types."""
        # ctypes and arrays are named by the expressions; the three names are
        # the whole vocabulary a declaration is written in.
        import ctypes

        from OpenGL import arrays

        types = self._types
        if isinstance(types, str):  # from the C table, comma-joined
            types = types.split(',')
        namespace = None
        resolved = []
        for text in types:
            key = (self.api, text)
            found = _types_cache.get(key)
            if found is None:
                if namespace is None:
                    namespace = {
                        'ctypes': ctypes,
                        'arrays': arrays,
                        '_cs': importlib.import_module(
                            'OpenGL.raw.%s._types' % (self.api,)
                        ),
                    }
                # The text was written by the generator out of the shipped
                # tree; it is our own source arriving by a longer road.
                found = _types_cache[key] = eval(text, namespace)
            resolved.append(found)
        return resolved

    def __call__(self):
        """The ctypes binding the declaration describes."""
        from OpenGL import platform

        types = self._resolve_types()
        errors = importlib.import_module('OpenGL.raw.%s._errors' % (self.api,))
        arguments = self._arguments
        if isinstance(arguments, str):
            arguments = [name for name in arguments.split(',') if name]
        # nullFunction rather than createFunction: createFunction hands back
        # the C entry point where there is one, and what wants a binding here
        # wants the thing underneath it.
        return platform.nullFunction(
            self.name,
            getattr(platform.PLATFORM, self.api, None) or platform.PLATFORM.GL,
            resultType=types[0],
            argTypes=tuple(types[1:]),
            doc=None,
            argNames=tuple(arguments),
            extension=self.extension,
            module=self.module,
            error_checker=errors._error_checker,
        )


def clear_caches():
    """Forget which source answered.  For the tests that compare them."""
    global _extension
    _extension = None
    _data.clear()
    _namespaces.clear()
    _types_cache.clear()
