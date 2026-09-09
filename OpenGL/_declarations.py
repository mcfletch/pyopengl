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

import ast
import importlib
import importlib.resources
import os

__all__ = [
    'define',
    'contents_for',
    'clear_caches',
    'table_path',
    'Declaration',
    'resolve_type',
]

#: Where the marshalled declarations live inside the package, as path segments
#: rather than as a path: they have to be reachable through whatever loader the
#: package was imported by, and a zip or a frozen application is not a
#: directory.
DATA = ('raw', '_declarations')


def _table(name):
    """One shipped table, as a resource rather than as a filename.

    A path built from ``__file__`` names nothing when the package is a zip, a
    frozen application, or anything else that is not a directory on disk.  With
    the generated modules no longer shipped these tables are the only
    description of :mod:`OpenGL.raw` there is, so they are read the way package
    data has to be read.
    """
    resource = importlib.resources.files('OpenGL')
    for part in DATA + (name,):
        resource = resource / part
    return resource


def _read_table(name):
    """The unmarshalled contents of one shipped table.

    Failure to read one is fatal rather than empty.  An empty table means "this
    API declares nothing", which is indistinguishable from a working
    installation right up to the point where a module that ought to exist
    cannot be imported, several frames from the missing file.

    A table that is *there* but damaged -- a truncated extraction, a bad mirror,
    a filesystem that lost a block -- has to say so the same way.  ``marshal``
    is what reads these because it is the fastest thing in the standard library
    at the job, and the price is that malformed input raises whatever it happens
    to raise rather than one named error; catching the set is what turns that
    back into the sentence above.
    """
    import marshal

    try:
        blob = _table(name).read_bytes()
        return marshal.loads(blob)
    except (OSError, KeyError, EOFError, ValueError, TypeError) as error:
        raise ImportError(
            'PyOpenGL cannot read its declaration table %r (%s). Every module '
            'under OpenGL.raw is built from these tables, so this installation '
            'cannot work; they are package data and something has dropped or '
            'damaged them.' % (name, error)
        ) from error


#: One resolved path per API.  ``find_spec`` asks for every generated module
#: imported, and resolving the resource means an import lookup and a stat --
#: which is a cost per module, for an answer that cannot change during a run.
_table_paths = {}


def table_path(api):
    """The filesystem path of one table, or ``None`` where it is not a file.

    What a generated module reports as its ``__file__``.  Inside a zip or a
    frozen application there is no path to report, and saying nothing is better
    than naming something that cannot be opened.
    """
    if api not in _table_paths:
        try:
            path = os.fspath(_table('%s.dat' % (api,)))
        except TypeError:  # a resource that is not a file on disk
            path = None
        _table_paths[api] = path if path and os.path.exists(path) else None
    return _table_paths[api]

#: The APIs a declaration table is shipped for.  GLU, GLUT, GLE and OSMesa are
#: hand-maintained rather than registry-described, so they keep their modules.
APIS = ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'EGL', 'GLX', 'WGL')

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
    """The shipped declarations for one API, read once.

    An API with no table is not an error: GLU, GLUT, GLE and OSMesa are
    hand-maintained rather than registry-described, so nothing generates a
    table for them and their modules are shipped as files.  It is a *missing*
    table, for one of the APIs :data:`APIS` says is generated, that means a
    broken installation -- and :func:`_read_table` raises for that.
    """
    if api not in _data:
        _data[api] = _read_table('%s.dat' % (api,)) if api in APIS else {}
    return _data[api]


class _DataDeclarations:
    """The declaration tables, in the shape the finder asks the C for.

    The finder was written against the extension because that was the only
    source that could enumerate the generated modules.  With the modules gone
    the finder has to answer on the ctypes path too, and the tables hold the
    same facts -- so they answer the same two questions.
    """

    def module_names(self):
        names = []
        for api in APIS:
            names.extend(_data_source(api))
        return names

    def module_contents(self, module_name):
        return contents_for(module_name)


def data_declarations():
    """A declaration source backed by the shipped tables."""
    return _DataDeclarations()


def api_of(module_name):
    """``OpenGL.raw.GL.VERSION.GL_1_1`` names the GL API."""
    parts = module_name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


#: Per API, the names a core version declares.  See :func:`core_command_names`.
_core_commands = {}


def core_command_names(api):
    """The entry points a core version of ``api`` declares.

    An extension may re-specify a name a core version already has:
    ``GL_KHR_debug`` gave ``glGetPointerv`` the pnames that report a debug
    callback, and the entry point itself has been GL 1.1 since 1995.  What a
    caller reaches is settled by which module they imported from, and the gate
    that refuses an unadvertised extension has to know which names those are
    -- or importing from the extension's module answers that a GL 1.1 entry
    point does not exist, on a driver that has always had it.

    Read from the shipped tables, which is where the core versions are listed,
    and built once per API on the first gate that needs one.  The compiled
    layer is told the same fact at generation time, held as each command's
    ``alternates``; this is how the ctypes path comes to know it.
    """
    known = _core_commands.get(api)
    if known is not None:
        return known
    names = set()
    declarations = data_declarations()
    for module_name in declarations.module_names():
        if api_of(module_name) != api:
            continue
        contents = declarations.module_contents(module_name) or {}
        extension = contents.get('extension') or ''
        # The same rule BasePlatform.constructFunction applies: a core version
        # names itself GL_VERSION_1_1 or GL_ES_VERSION_3_2, so the token is not
        # always in the same place and the name is asked rather than the path.
        if extension and 'VERSION' not in extension.split('_'):
            continue
        names.update(command for command, _arguments, _types in contents['commands'])
    known = _core_commands[api] = frozenset(names)
    return known


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

    try:
        name, constants, commands, reexports = marshal.loads(blob)
    except (EOFError, ValueError, TypeError) as error:
        raise ImportError(
            'PyOpenGL cannot read the declarations for %r from its table (%s); '
            'the table is package data and something has damaged it.'
            % (module_name, error)
        ) from error
    return {
        'extension': name,
        'constants': constants,
        'commands': commands,
        'reexports': reexports,
    }


def annotations():
    """The customisation table: what each entry point wraps its call in."""
    global _annotations
    if _annotations is None:
        _annotations = _read_table('_annotations.dat')
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
    for parameter, __kind in declared:
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

    for __order, parameter, size in outputs:
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


def also(namespace, *modules):
    """Take from each of ``modules`` only the names ``namespace`` lacks.

    The modules are passed as objects rather than named, so the ``import`` that
    fetched them is an ordinary static one: a freezer reads those and bundles
    what they name, and a dynamic import here leaves the extension modules out
    of the bundle and the frozen application dying on its first import.

    A GL version adopts extensions wholesale -- 4.1 is
    ``ARB_separate_shader_objects`` and five others -- and the version module
    carries their names so that a client importing ``OpenGL.GL`` finds them.
    It must not take their *entry points* over its own.

    A command declared by both is declared twice, and the two differ in the one
    way that matters: the extension declaration is gated on the driver
    advertising the extension string, and the core one is not.  A driver is
    entitled to stop advertising an extension it has promoted, and a core
    profile commonly does -- macOS's 4.1 core profile does not list
    ``GL_ARB_separate_shader_objects`` -- so the gated declaration answers
    ``NullFunctionError`` for a function the context implements.

    Which is why this is not ``import *``: that runs after :func:`define` has
    put the version's own declarations in place, and takes them back out.  The
    C dispatch layer records the same pair the same way round, with the core
    name as the declaration and the extension as an alternate.
    """
    for module in modules:
        exported = getattr(module, '__all__', None)
        if exported is None:
            # What ``import *`` would have taken.
            exported = [key for key in vars(module) if not key.startswith('_')]
        for key in exported:
            namespace.setdefault(key, getattr(module, key))


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


#: The constructors a declared type may be built with.  A declaration's whole
#: vocabulary is an attribute lookup on one of three namespaces, or one of
#: these applied to such lookups -- and holding it to that is what makes
#: "the text is read, not executed" a fact rather than an intention.  Anything
#: else reachable from ``ctypes`` is a way for a data file to run code.
_TYPE_CONSTRUCTORS = ('POINTER', 'CFUNCTYPE', 'WINFUNCTYPE')


def _accepting(kind):
    """The binding's form of a declared type: the same C type, taking more.

    A declaration states the C signature, and for most parameters that is also
    what Python passes.  Where it is not -- an array of strings is declared
    ``GLchar *const *``, and a caller has a list of strings -- the type the
    binding is built with is one that converts, so that the ctypes path accepts
    what the C dispatch path accepts.  It is the same C type either way, and
    what a caller could pass before is still passed unchanged.
    """
    from OpenGL import _string_array

    if kind is _string_array.CHAR_POINTER_ARRAY:
        return _string_array.StringArray
    return kind


def resolve_type(text, namespace):
    """``_cs.GLenum``, ``ctypes.POINTER(_cs.GLchar)``, ``None`` -- as a value.

    ``namespace`` offers the three names a declaration is written against:
    ``ctypes``, ``arrays`` and ``_cs``, the API's own types module.
    """
    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError:
        raise ValueError('not a type expression: %r' % (text,)) from None
    return _evaluate(tree.body, text, namespace)


def _evaluate(node, text, namespace):
    if isinstance(node, ast.Constant):
        if node.value is None:
            return None
        raise ValueError('not a type expression: %r' % (text,))
    if isinstance(node, ast.Name):
        try:
            return namespace[node.id]
        except KeyError:
            raise ValueError(
                'unknown name %r in type expression %r' % (node.id, text)
            ) from None
    if isinstance(node, ast.Attribute):
        # A dunder is Python's own machinery -- __class__, __globals__,
        # __subclasses__ -- and reaching it from a data file is a way out of the
        # three namespaces.  Leading underscores alone are not: GLX declares
        # __GLXextFuncPtr, which is an ordinary type of ours.
        if node.attr.startswith('__') and node.attr.endswith('__'):
            raise ValueError(
                'not a type expression: %r names %r' % (text, node.attr)
            )
        return getattr(_evaluate(node.value, text, namespace), node.attr)
    if isinstance(node, ast.Call):
        if node.keywords or not isinstance(node.func, ast.Attribute):
            raise ValueError('not a type expression: %r' % (text,))
        if node.func.attr not in _TYPE_CONSTRUCTORS:
            raise ValueError(
                'not a type constructor: %r calls %r' % (text, node.func.attr)
            )
        function = _evaluate(node.func, text, namespace)
        return function(
            *[_evaluate(argument, text, namespace) for argument in node.args]
        )
    raise ValueError('not a type expression: %r' % (text,))


def as_sequence(value):
    """``'a,b'`` or ``('a', 'b')`` -- both are a sequence of items.

    The C table hands these over comma-joined and the marshalled tables keep
    them as tuples.  Either way they are names and expressions, and the
    difference is not one anything below here should have to know.
    """
    if isinstance(value, str):
        return value.split(',')
    return list(value)


class Declaration:
    """What a generated module's ``@_p.types(...) def glFoo(...)`` said.

    Held as the text it was written in and turned into a ctypes binding on the
    first call that asks for one, because most entry points never see one.

    One class for both routes into it: the C extension carries the declarations
    in ``.rodata`` and the shipped tables carry the same ones marshalled, and
    they describe the same entry points.
    """

    __slots__ = ('_arguments', '_types', 'api', 'extension', 'module', 'name')

    def __init__(self, api, name, extension, module, arguments, types):
        self.api = api
        self.name = name
        self.extension = extension
        self.module = module
        self._arguments = tuple(name for name in as_sequence(arguments) if name)
        self._types = tuple(as_sequence(types))

    def _resolve_types(self):
        """``('None', '_cs.GLenum', 'arrays.GLfloatArray')`` as the types."""
        # ctypes and arrays are named by the expressions; the three names are
        # the whole vocabulary a declaration is written in.
        import ctypes

        from OpenGL import arrays

        namespace = None
        resolved = []
        for text in self._types:
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
                found = _types_cache[key] = _accepting(
                    resolve_type(text, namespace)
                )
            resolved.append(found)
        return resolved

    def __call__(self):
        """The ctypes binding the declaration describes."""
        from OpenGL import platform

        types = self._resolve_types()
        errors = importlib.import_module('OpenGL.raw.%s._errors' % (self.api,))
        # nullFunction rather than createFunction: createFunction hands back
        # the C entry point where there is one, and what wants a binding here
        # wants the thing underneath it.
        return platform.nullFunction(
            self.name,
            getattr(platform.PLATFORM, self.api, None) or platform.PLATFORM.GL,
            resultType=types[0],
            argTypes=tuple(types[1:]),
            doc=None,
            argNames=self._arguments,
            extension=self.extension,
            module=self.module,
            error_checker=errors._error_checker,
        )


def clear_caches():
    """Forget which source answered.  For the tests that compare them."""
    global _extension, _annotations
    _extension = None
    _annotations = None
    _data.clear()
    _namespaces.clear()
    _types_cache.clear()
    _table_paths.clear()
    _core_commands.clear()
