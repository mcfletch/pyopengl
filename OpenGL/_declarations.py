"""Declarations for the ``OpenGL.raw`` modules, read from generated tables.

Each ``OpenGL.raw`` module declares an extension name, a set of constants and
a set of entry points.  A friendly module (the hand-written module a program
imports, such as ``OpenGL.GL.VERSION.GL_1_1``) calls :func:`define`, which
writes those names straight into its namespace.  No ``OpenGL.raw`` module
object is built.

The declarations come from one of two sources, depending on the build:

* the C dispatch extension, which keeps them in ``.rodata`` and decodes them on
  first use;
* ``OpenGL/raw/_declarations/<API>.dat``, used by an installation without the
  compiled extension.

``python src/regenerate_c.py`` writes both sources in one pass, from the
registry and the shipped tree, so they hold the same declarations.
"""

import ast
import importlib
import importlib.resources
import os

__all__ = [
    'define',
    'contents_for',
    'declared_commands',
    'ctypes_entry_point',
    'clear_caches',
    'table_path',
    'Declaration',
    'resolve_type',
]

#: Where the marshalled declarations live inside the package, as path segments.
#: They are read through the package's loader, which may be a zip or a frozen
#: application instead of a directory.
DATA = ('raw', '_declarations')


def _table(name):
    """Return one shipped table as an importlib resource.

    A path built from ``__file__`` does not exist when the package is a zip, a
    frozen application, or anything else that is not a directory on disk.
    The tables are the only description of :mod:`OpenGL.raw` that ships, so
    they are read as package data.
    """
    resource = importlib.resources.files('OpenGL')
    for part in DATA + (name,):
        resource = resource / part
    return resource


def _read_table(name):
    """Return the unmarshalled contents of one shipped table.

    A table that cannot be read raises :class:`ImportError`.  Returning an
    empty table would mean "this API declares nothing", and the failure would
    surface later as a missing module, several frames from the missing file.

    A damaged table (a truncated extraction, a bad mirror, a lost disk block)
    raises the same error.  ``marshal`` is the fastest reader in the standard
    library, but malformed input makes it raise one of several exception
    types.  The ``except`` clause catches all of them.
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


#: One resolved path per API.  ``find_spec`` asks for it on every generated
#: module import, and resolving the resource costs an import lookup and a stat.
#: The path cannot change during a run.
_table_paths = {}


def table_path(api):
    """Return the filesystem path of one table, or ``None`` if it is not a file.

    A generated module reports this path as its ``__file__``.  Inside a zip or
    a frozen application the table has no path, so the result is ``None``
    instead of a path that cannot be opened.
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

#: The customisations, read from the shipped table on first use.  Each one is
#: the equivalent of a chain of wrapper.wrapper(...) calls on an entry point.
_annotations = None

#: Resolved type expressions, keyed by ``(api, text)``.  There are few distinct
#: expressions, but ``_cs.GLenum`` alone appears thousands of times.  Without
#: this cache, evaluating them is the largest cost of importing without the C
#: extension.
_types_cache = {}

#: The C extension, looked up once, or False when there is none to use.
_extension = None

#: The namespace each generated module declares, built for the first friendly
#: module that needs it and copied after that.  GL_1_1 re-exports GL_1_0,
#: GL_1_2 re-exports GL_1_1, and forty friendly modules depend on the chain.
#: This cache stops the chain being rebuilt for each of them.
_namespaces = {}


def _c_source():
    """Return the C dispatch extension, or False if it is not in use."""
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
                # install() fills `entry_points`.  No other code path does.
                if _dispatch.install():
                    _extension = _dispatch._c
    return _extension


def _data_source(api):
    """Return the shipped declarations for one API, read once.

    An API outside :data:`APIS` returns an empty mapping.  GLU, GLUT, GLE and
    OSMesa are maintained by hand, so no table is generated for them and their
    modules ship as files.  A missing table for an API in :data:`APIS` means a
    broken installation, and :func:`_read_table` raises for it.
    """
    if api not in _data:
        _data[api] = _read_table('%s.dat' % (api,)) if api in APIS else {}
    return _data[api]


class _DataDeclarations:
    """The declaration tables, with the two methods the finder calls on the C.

    The finder calls ``module_names()`` and ``module_contents()`` on the C
    extension.  On the ctypes path it calls the same methods on this class,
    which reads the shipped tables.
    """

    def module_names(self):
        names = []
        for api in APIS:
            names.extend(_data_source(api))
        return names

    def module_contents(self, module_name):
        return contents_for(module_name)


def data_declarations():
    """Return a declaration source backed by the shipped tables."""
    return _DataDeclarations()


def api_of(module_name):
    """Return the API a module name belongs to: ``'GL'`` for ``OpenGL.raw.GL.VERSION.GL_1_1``."""
    parts = module_name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


#: Per API, the names a core version declares.  See :func:`core_command_names`.
_core_commands = {}


def core_command_names(api):
    """Return the frozenset of entry points a core version of ``api`` declares.

    An extension may re-specify an entry point a core version already has.
    ``GL_KHR_debug`` adds pnames to ``glGetPointerv`` for the debug callback,
    and ``glGetPointerv`` has been core since GL 1.1 in 1995.  The gate that
    refuses entry points of an unadvertised extension uses this set to let
    core entry points through.  Without it, importing ``glGetPointerv`` from
    the extension's module would report a GL 1.1 entry point as missing.

    The set is read from the shipped tables and built once per API, on first
    use.  The C dispatch layer gets the same information at generation time,
    in each command's ``alternates``.
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
        # The same rule BasePlatform.constructFunction applies.  A core version
        # is named GL_VERSION_1_1 or GL_ES_VERSION_3_2, so the VERSION token is
        # not always in the same position, and the extension name is checked
        # instead of the module path.
        if extension and 'VERSION' not in extension.split('_'):
            continue
        names.update(command for command, _arguments, _types in contents['commands'])
    known = _core_commands[api] = frozenset(names)
    return known


def contents_for(module_name):
    """Return what one generated module declares, or None if no source has it.

    The result is a mapping with ``extension``, ``constants``, ``commands`` and
    ``reexports`` keys.  Both sources return the same shape, so callers do not
    depend on which source is in use.
    """
    extension = _c_source()
    if extension:
        # Both sources are generated together and list the same modules.  A
        # module missing from the extension is missing from the table too, so
        # the half-megabyte table is not loaded to check.
        return extension.module_contents(module_name)
    blob = _data_source(api_of(module_name)).get(module_name)
    if blob is None:
        return None
    return _decoded(module_name, blob)


def _decoded(module_name, blob):
    """Decode one module's marshalled table entry into the :func:`contents_for` mapping."""
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


def declared_commands(api):
    """Yield ``(module name, command, argument names, types)`` for each command in ``api``'s table.

    Reads the shipped table, which every installation has, with or without the
    C extension.  ``types`` is the result type followed by one type per
    argument, as text.  A command declared by two modules appears once for
    each.
    """
    for module_name, blob in sorted(_data_source(api).items()):
        for command, arguments, types in _decoded(module_name, blob)['commands']:
            yield (
                module_name,
                command,
                tuple(name for name in as_sequence(arguments) if name),
                tuple(as_sequence(types)),
            )


def ctypes_entry_point(module_name, name):
    """Return the customised ctypes binding for ``name`` from ``module_name``.

    The result is the entry point a friendly module gets from ``define(...)``
    under the ctypes implementation.  It is built even when this process runs
    the C implementation.
    """
    contents = contents_for(module_name)
    if contents is None:
        raise KeyError('no table describes %s' % (module_name,))
    declared = {
        command: (arguments, types)
        for command, arguments, types in contents['commands']
    }
    if name not in declared:
        raise KeyError('%s declares no %s' % (module_name, name))
    arguments, types = declared[name]
    api = api_of(module_name)
    binding = Declaration(
        api, name, contents['extension'], module_name, arguments, types
    )()
    return customise_entry(binding, api, name, _array_parameters(arguments, types))


def annotations():
    """Return the customisation table, which says how each entry point is wrapped."""
    global _annotations
    if _annotations is None:
        _annotations = _read_table('_annotations.dat')
    return _annotations


def customise_entry(entry, api, name, declared):
    """Return ``entry`` wrapped as the customisation table describes.

    Input parameters follow these rules:

    * a parameter gets an array conversion when the table marks it ``array``;
    * the length comes from the table when it has one, which is rare, and
      ``setInputArraySize(x, None)`` sets a conversion with no length;
    * a ``from-argument`` length is a minimum of ``count * multiplier``
      elements, read from another argument and applied with
      ``setInputArrayCount``.

    The table marks array parameters because the declared type cannot.
    ``glDrawElements`` and similar calls declare their array as
    ``ctypes.c_void_p``, since it may be a client pointer or a buffer offset.
    Inferring arrays from the type would miss those and add conversions to
    parameters the friendly layer never wrapped, which changes 171 entry
    points.

    Output parameters are rebuilt from the same table.  Besides a size,
    ``setOutput`` needs the argument whose value gives the size and whether a
    caller may pass the array in.  The table holds the argument.  Passing the
    array in is allowed for all 688 calls in the tree, so it is not recorded
    per entry.  Three of the four size kinds are handled here: a fixed count,
    a count read from another argument, and the ``_glgets`` table.  An image
    size depends on the format and type arguments together, so the modules
    that need one keep their own wrapper chain.

    A ``GLProc`` is returned unchanged, because the C implementation already
    does all of this, as ``implements_friendly`` records.
    """
    entry_annotations = annotations().get('%s.%s' % (api, name))
    parameters = (entry_annotations or {}).get('parameters', {})
    if not parameters and not declared:
        return entry
    from OpenGL import wrapper

    outputs = _output_parameters(parameters)
    if outputs is None:
        # An output size these rules cannot express.  The module keeps its own
        # chain.  Wrapping only the inputs would produce a wrapper that looks
        # complete and is not.
        return entry

    built = entry
    for parameter, __kind in declared:
        bits = parameters.get(parameter, {})
        if bits.get('out'):
            continue          # rebuilt below, in the order the chain used
        if not bits.get('array'):
            continue
        size = bits.get('size') or {}
        if built is entry:
            built = wrapper.wrapper(entry)
        if size.get('kind') == 'from-argument':
            built = built.setInputArrayCount(
                parameter, size['argument'], size['multiplier']
            )
        else:
            length = size['count'] if size.get('kind') == 'fixed' else None
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
                size=_scaled_by(size['divisor'], size['multiplier']),
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


#: The output size kinds :func:`customise_entry` handles.  ``image`` is left
#: out because an image size depends on the format and type arguments
#: together, and the modules that need one keep their own chain.
_OUTPUT_SIZE_KINDS = frozenset(['fixed', 'from-argument', 'glget-table'])


def _output_parameters(parameters):
    """Return ``[(order, name, size), ...]``, or ``None`` if a size kind is unsupported.

    The order is the order the wrapper chain applied the outputs in.  The
    table records it because ``setOutput`` builds the Python signature, and
    argument order matters there.
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


def _scaled_by(divisor, multiplier):
    """Return a ``setOutput`` size function: the argument's value times ``multiplier // divisor``."""
    if divisor == 1 and multiplier == 1:
        return lambda value: (value,)
    return lambda value: (value * multiplier // divisor,)


def _import(name):
    import importlib

    return importlib.import_module(name)


def also(namespace, *modules):
    """Copy into ``namespace`` the names from ``modules`` that it does not already have.

    The modules are passed as objects, so the caller imports them with an
    ordinary static ``import``.  Freezers bundle what static imports name.  A
    dynamic import here would leave the extension modules out of a frozen
    application, which would then fail on its first import.

    A GL version includes whole extensions (4.1 includes
    ``ARB_separate_shader_objects`` and five others).  The version module
    carries their names so that a client importing ``OpenGL.GL`` finds them,
    but it keeps its own entry points for commands both declare.

    The two declarations of such a command differ in one way.  The extension
    declaration works only if the driver advertises the extension string, and
    the core declaration has no such check.  Drivers may stop advertising an
    extension once it is core, and core profiles often do: the macOS 4.1 core
    profile does not list ``GL_ARB_separate_shader_objects``.  The extension
    declaration would then raise ``NullFunctionError`` for a function the
    context implements.

    ``import *`` would run after :func:`define` and replace the version's own
    declarations, so this function is used instead.  The C dispatch layer
    stores the same pair the same way, with the core name as the declaration
    and the extension as an alternate.
    """
    for module in modules:
        exported = getattr(module, '__all__', None)
        if exported is None:
            # What ``import *`` would have taken.
            exported = [key for key in vars(module) if not key.startswith('_')]
        for key in exported:
            namespace.setdefault(key, getattr(module, key))


def define(namespace, module_name):
    """Define in ``namespace`` every name ``module_name`` declares, and return its extension name.

    Each command is customised from the annotation table as it is defined.
    The customisations are the array conversions and output parameters that
    make its Python signature differ from the C one.  A friendly module must
    not add its own ``wrapper.wrapper(...).setInputArraySize(...)`` chain:
    applying a customisation twice makes ``wrapper`` raise ``Double wrapping
    of output parameter``.  Code in the module after this call sees the
    customised entry points.

    A friendly module calls it like this::

        _EXTENSION_NAME = define(globals(), 'OpenGL.raw.GL.VERSION.GL_1_1')

    The caller stores the returned extension name as ``_EXTENSION_NAME``.
    """
    built, extension = _build(module_name)
    namespace.update(built)
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
    """Return ``[(name, 'array' | 'scalar'), ...]`` parsed from the declaration's text.

    The customisation table does not record which parameters are arrays.
    That comes from the declared type.  The type is read from the text
    because reading ``argtypes`` on a C entry point builds its ctypes binding,
    which the import path avoids.  Reading ``argtypes`` here would build 1,143
    bindings.
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
    """Return ``(names, extension name)`` for one generated module.

    The result is built once and cached in ``_namespaces``.
    """
    remembered = _namespaces.get(module_name)
    if remembered is not None:
        return remembered

    contents = contents_for(module_name)
    if contents is None:
        # No source describes it.  The module is one of the few written by
        # hand, or this checkout has neither the extension nor the tables.
        # Import the module itself.
        module = importlib.import_module(module_name)
        exported = getattr(module, '__all__', None)
        if exported is None:
            # The names ``import *`` would take.  Private names are the
            # module's internals and are skipped.
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

    from OpenGL.constant import declared

    for key, value in contents['constants'].items():
        built[key] = declared(key, value, module_name)

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
    """Return the callable a client gets for one entry point.

    That is the C implementation when there is one, and the ctypes binding
    otherwise.  With a C implementation, the ctypes binding is only needed
    when a client demotes the entry point to ctypes.  That happens for a few
    dozen of nearly five thousand entry points, so the declaration is stored
    and the binding is built on demand.
    """
    from OpenGL._dispatch import entry_points, support

    proc = entry_points.get((api, name))
    if proc is None:
        # No C entry point, so the ctypes binding is the entry point.  Build it
        # now and do not register a factory.
        return Declaration(api, name, extension, module_name, arguments, types)()
    # With a C entry point, the binding is only used for demotion and for the
    # argtypes/restype/DLL attributes.  Few callers use either, so the
    # declaration is registered and the binding built on first request.
    support.register_ctypes_factory(
        api, name, Declaration(api, name, extension, module_name, arguments, types)
    )
    support.register_module(api, name, module_name)
    return proc


#: The constructors a declared type may be built with.  A type expression is
#: an attribute lookup on one of three namespaces, or one of these
#: constructors applied to such lookups.  Limiting expressions to that set
#: means the text is evaluated without being executed.  Other callables in
#: ``ctypes`` could let a data file run code.
_TYPE_CONSTRUCTORS = ('POINTER', 'CFUNCTYPE', 'WINFUNCTYPE')


def _accepting(kind):
    """Return the type a ctypes binding uses for a declared type.

    For most parameters the C type is also what Python passes.  An array of
    strings is declared ``GLchar *const *``, but a caller passes a list of
    strings.  For that type the binding uses ``_string_array.StringArray``,
    which converts the list, so the ctypes path accepts what the C dispatch
    path accepts.  The C type is the same, and values that ``GLchar *const *``
    accepts still pass unchanged.
    """
    from OpenGL import _string_array

    if kind is _string_array.CHAR_POINTER_ARRAY:
        return _string_array.StringArray
    return kind


def resolve_type(text, namespace):
    """Evaluate a type expression such as ``_cs.GLenum``, ``ctypes.POINTER(_cs.GLchar)`` or ``None``.

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
        # Dunder attributes (__class__, __globals__, __subclasses__) lead out
        # of the three namespaces, so they are refused.  Leading underscores
        # alone are allowed: GLX declares __GLXextFuncPtr, an ordinary type.
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
    """Return ``'a,b'`` or ``('a', 'b')`` as the list ``['a', 'b']``.

    The C table passes names and type expressions as comma-joined strings.
    The marshalled tables keep them as tuples.  Callers get a list from
    either.
    """
    if isinstance(value, str):
        return value.split(',')
    return list(value)


class Declaration:
    """One entry point declaration, equivalent to ``@_p.types(...) def glFoo(...)``.

    The declaration is stored as text.  Calling the instance builds the ctypes
    binding, which most entry points never need.

    Both declaration sources use this class.  The C extension keeps the
    declarations in ``.rodata`` and the shipped tables keep the same ones
    marshalled.
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
        """Resolve type text such as ``('None', '_cs.GLenum', 'arrays.GLfloatArray')``."""
        # Type expressions use only three names: ctypes, arrays and _cs.
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
        """Build and return the ctypes binding the declaration describes."""
        from OpenGL import platform

        types = self._resolve_types()
        errors = importlib.import_module('OpenGL.raw.%s._errors' % (self.api,))
        # nullFunction, because createFunction returns the C entry point when
        # there is one, and the caller here needs the ctypes binding.
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
    """Clear the cached source and tables, for tests that compare the two sources."""
    global _extension, _annotations
    _extension = None
    _annotations = None
    _data.clear()
    _namespaces.clear()
    _types_cache.clear()
    _table_paths.clear()
    _core_commands.clear()
