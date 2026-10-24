"""Python functions the C dispatch layer calls back into.

None of these run on the hot path.  They resolve a proc address once per
entry point per context, convert an array the fast path did not match, raise
GL errors, and build the ctypes binding an entry point falls back to when a
client demotes it.
"""

import ctypes
import sys

from OpenGL import arrays, error, platform
from OpenGL._bytes import as_8_bit

__all__ = [
    'resolve',
    'as_pointer',
    'opaque',
    'raise_gl_error',
    'ctypes_callable',
    'module_for',
    'array_type_map',
    'swallowed_for',
]

#: (api, name) -> the ctypes binding, recorded when the C entry point is
#: installed over it.  Demotion and the ``argtypes``/``restype``/``DLL``
#: attributes read from here.
_ctypes_bindings = {}
_modules = {}

#: The exception each API raises for its own errors, by API name.  EGL's codes
#: differ from GL's and have their own class, so the class comes from the API
#: whose call failed instead of from one shared default.
_error_classes = {}


def register_error_class(api, errorClass):
    """Record the exception class ``api`` raises for its errors."""
    _error_classes[api] = errorClass

_API_NAMES = ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'GLX', 'WGL', 'EGL')

#: Which entry point the C layer is currently resolving.  The C passes the API
#: as an index, so the mapping back to a library lives here.
_DLL_ATTRIBUTE = {
    'GL': 'GL',
    'GLES1': 'GLES1',
    'GLES2': 'GLES2',
    'GLES3': 'GLES3',
    'GLSC2': 'GLES2',
    'GLX': 'GL',
    'WGL': 'GL',
    'EGL': 'EGL',
}


def _dll_for(api):
    return getattr(platform.PLATFORM, _DLL_ATTRIBUTE.get(api, 'GL'), None)


def resolve(name, extension, alternates, api_index):
    """Return the address of an entry point in the current context, or None.

    This applies the same rules as ``BasePlatform.constructFunction``, so an
    entry point the ctypes path refuses is refused here too.  It runs once per
    entry point per context.

    ``alternates`` is a comma-separated list of the other extensions that
    declare the same command.  Many commands are declared by two extensions.
    ``glUniform1i64NV``, for example, is in both ``GL_NV_gpu_shader5`` and
    ``GL_AMD_gpu_shader_int64``.  A driver advertising either has the
    function, so one match is enough.
    """
    from OpenGL import _dispatch, dispatch as _dispatch_api

    # The first resolution is the first point at which a context exists.  It
    # installs the current-context getter and offers the context debug-output
    # error checking.
    _dispatch.install_context_getter()
    _dispatch_api.offer_debug_output()
    api = _API_NAMES[api_index]
    platform_ = platform.PLATFORM
    is_core = (not extension) or 'VERSION' in extension.split('_')
    if not is_core and not _extension_gate_passes(platform_, extension, alternates):
        return None
    if is_core:
        # The API's own library first, then the platform's secondary
        # libraries.  On Windows the pixel-format calls and SwapBuffers are in
        # GDI, and opengl32 does not export them.  constructFunction falls
        # back the same way, so both paths bind the same set of functions.
        dll = _dll_for(api)
        libraries = [dll] if dll is not None else []
        libraries.extend(platform_.secondaryLibraries())
        for library in libraries:
            try:
                function = getattr(library, name)
            except AttributeError:
                continue
            address = ctypes.cast(function, ctypes.c_void_p).value
            if address:
                return address
    try:
        pointer = platform_.getExtensionProcedure(as_8_bit(name))
    except Exception:
        pointer = None
    if pointer:
        return int(pointer)
    return None


def _extension_gate_passes(platform_, extension, alternates):
    """Return whether the extension check allows this command.

    The check reads the context's extension string, and no GL query is legal
    between ``glBegin`` and ``glEnd``.  Immediate-mode extension commands such
    as ``glColor3hNV``, ``glPrimitiveRestartNV`` and ``glMultiTexCoord2fARB``
    can only be called inside a Begin/End block, so that is where they are
    first resolved.  Querying there returns no extensions, reports a command
    the driver has as undefined, and records GL_INVALID_OPERATION against the
    block.

    Inside a block the check is skipped, and the address returned by the
    windowing system decides instead.  Outside a block the check applies as
    usual.
    """
    if error.inside_begin_block():
        return True
    return _any_extension_present(platform_, extension, alternates)


def _any_extension_present(platform_, extension, alternates):
    """Return whether the context advertises an extension with the command."""
    for name in (extension, *(alternates or '').split(',')):
        if not name:
            continue
        if 'VERSION' in name.split('_'):
            return True  # a core version declares it; no string to check
        if platform_.checkExtension(name):
            return True
    return False


def is_pointer_sized(value):
    """Return whether ``value`` is a ctypes scalar whose value is an address.

    ``c_void_p`` is the common case.  WGL's handles (``HDC``, ``HGLRC``,
    ``HPBUFFERARB``) are why this checks the type code instead of a class.
    They are pointer-sized simple types instead of pointer classes, because
    ctypes shares every reference to ``c_void_p`` and a shared one would
    disable the array machinery for every other use.  So
    ``isinstance(handle, c_void_p)`` is False for them, while ``.value`` is the
    handle itself.
    """
    return (isinstance(value, ctypes._SimpleCData)
            and getattr(type(value), '_type_', None) == 'P')


def as_pointer(value):
    """Return the address of a value a client passes as a pointer argument.

    Accepts what the ctypes layer accepts: plain integers, ctypes instances,
    the opaque pointer classes, and the byref result the ctypes array handlers
    return from ``dataPointer``.  A byref result holds a reference to its
    object instead of an address.
    """
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    referent = getattr(value, '_obj', None)
    if referent is not None:
        return ctypes.addressof(referent)
    # A c_void_p's value is an address; a c_int's is not.  Reading `.value`
    # from any object with one would turn ctypes.c_int(1234) into address
    # 1234, so the type is checked instead of the attributes.  Pointer-sized
    # scalars and the opaque handle classes (pointer subclasses) are handled
    # here.  The fallbacks below return the address of the object itself.
    # For a handle, that would pass the display driver a pointer into the
    # interpreter's heap, with no error raised.
    if is_pointer_sized(value):
        return value.value or 0
    if isinstance(value, ctypes._Pointer):
        return ctypes.cast(value, ctypes.c_void_p).value or 0
    inner = getattr(value, '_as_parameter_', None)
    if isinstance(inner, int):
        return inner
    try:
        return ctypes.cast(value, ctypes.c_void_p).value or 0
    except (ctypes.ArgumentError, TypeError):
        pass
    try:
        return ctypes.addressof(value)
    except TypeError:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        raise TypeError('cannot use %r as a pointer' % (type(value).__name__,)) from None


_opaque_classes = {}


#: The modules that declare the handle classes.  The C layer must use these
#: classes, not new ones.  The ctypes bindings name them in their argtypes and
#: restypes, so a GLsync of a different class with the same name is rejected by
#: any entry point still on the ctypes path.  A WGL handle not found here would
#: come back as a new pointer class instead of the integer ctypes produces.
_OPAQUE_MODULES = (
    'OpenGL.raw.GL._types',
    'OpenGL.raw.EGL._types',
    'OpenGL.raw.WGL._types',
    'OpenGL.raw.GLX._types',
)


def _declared_class(type_name):
    """Return the class the bindings declare for ``type_name``, cached.

    A name no module declares gets a new opaque pointer class, as on the
    ctypes path.
    """
    import importlib

    cls = _opaque_classes.get(type_name)
    if cls is not None:
        return cls
    for module_name in _OPAQUE_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        cls = getattr(module, type_name, None)
        if cls is not None:
            break
    if cls is None:
        from OpenGL import _opaque

        cls = _opaque.opaque_pointer_cls(type_name)
    _opaque_classes[type_name] = cls
    return cls


def opaque(address, type_name):
    """Return the object for an opaque return value, matching the ctypes path.

    A pointer class, such as GL's ``GLsync`` or EGL's ``EGLDisplay``, gives an
    instance of that class.  Callers comparing two such values rely on this.
    A pointer-sized scalar, which is how WGL declares ``HDC`` and similar
    handles, gives a plain integer, because ctypes converts such a result to
    one.  Both implementations return the same types, so a program sees the
    same values on either.
    """
    cls = _declared_class(type_name)
    if issubclass(cls, ctypes._SimpleCData) and getattr(cls, '_type_', None) == 'P':
        return address
    return ctypes.cast(ctypes.c_void_p(address), cls)


def raise_gl_error(code, name, arguments=None, api=None):
    """Raise the exception for a failed call.

    The exception carries the call's arguments, which identify the failing
    call.  Clients read ``err.pyArgs``, which the ctypes path leaves empty.

    ``baseOperation`` is the entry point instead of its name, so
    ``err.baseOperation.__name__`` works and ``format_baseOperation`` in
    ``error.py`` takes its entry-point branch.  ``cArguments`` is filled as
    well as ``cArgs``, because ``GLError``'s docstring documents it.
    """
    raise _error_classes.get(api, error.GLError)(
        err=code,
        baseOperation=_entry_point_or_name(api, name),
        pyArgs=arguments,
        cArgs=arguments,
        cArguments=arguments,
    )


def _entry_point_or_name(api, name):
    """Return the entry point that failed, or its name if the API is unknown.

    Clients read ``err.baseOperation.__name__``, and ``format_baseOperation``
    in ``error.py`` expects an entry point, so the exception carries the entry
    point object wherever one exists.
    """
    if api is None:
        return name
    from OpenGL._dispatch import entry_points

    return entry_points.get((api, name)) or name


def register_ctypes_binding(api, name, binding):
    """Record the ctypes binding a C entry point replaced."""
    _ctypes_bindings[(api, name)] = binding


def register_module(api, name, module):
    _modules[(api, name)] = module


#: Factories for the ctypes bindings of entry points whose declarations have
#: not been run.  Filled by the module finder, which replaces the module files
#: that ran them.
_ctypes_factories = {}


def register_ctypes_factory(api, name, factory):
    """Record the factory for the ctypes binding an entry point demotes to."""
    _ctypes_factories.setdefault((api, name), factory)


def ctypes_callable(name, api=None):
    """Return an entry point's ctypes binding, for demotion and attributes.

    ``api`` selects the binding.  ``glClear`` exists in GL and in GLES2 as
    separate bindings from separate libraries.  Taking the first name that
    matches can return the desktop GL function for a GLES2 entry point, and on
    a system with both, demoting would then bind the wrong library.  The C
    layer passes ``api``.  With ``None``, the first match in API order is
    returned.
    """
    order = (api,) + tuple(_API_NAMES) if api else tuple(_API_NAMES)
    for candidate in order:
        binding = _ctypes_bindings.get((candidate, name))
        if binding is not None:
            return binding
    for candidate in order:
        factory = _ctypes_factories.get((candidate, name))
        if factory is not None:
            binding = factory()
            _ctypes_bindings[(candidate, name)] = binding
            return binding
    raise AttributeError('no ctypes binding recorded for %s' % (name,))


def module_for(name, api=None):
    """Return the name of the module that declared this entry point.

    ``api`` is needed for the same reason as in :func:`ctypes_callable`.
    Without it, ``GLES2.glClear.__module__`` reports the desktop GL module.
    """
    order = (api,) + tuple(_API_NAMES) if api else tuple(_API_NAMES)
    for candidate in order:
        module = _modules.get((candidate, name))
        if module is not None:
            return module
    return 'OpenGL'


def swallowed_for(proc):
    """Return the customisations a chain absorbed, as a mapping (may be empty).

    The record is kept on the chain: the ``GLProc`` a friendly module holds
    once the C layer has absorbed one of its customisation calls.  An entry
    point itself, and anything that is not a ``GLProc``, has an empty record.
    """
    return getattr(proc, '_swallowed', None) or {}


def record_custom(proc, method, args):
    """Record a customisation the C layer performs; return the chain.

    A friendly module may build a derived function from an entry point, such
    as glVertexPointerd(array) from glVertexPointer(size, type, stride,
    pointer).  It does so by continuing the chain with a call that changes the
    arity.  That call must demote, and the wrapper it demotes to needs the
    customisations its chain absorbed before it.  Each derived function has
    its own customisations (glVertexPointerf converts to float, and
    glVertexPointerd to double), so the record belongs to the chain.
    ``proc._chained()`` returns `proc` if it is already a chain, and a new
    ``GLProc`` for the same command if it is the entry point.
    """
    chain = proc._chained()
    # Keyed by what it customises.  If a chain gives one argument two
    # converters, the second is used, as on a wrapper.
    chain._swallowed[(method, args[0] if args else None)] = tuple(args)
    return chain


def _replayed(proc, customisations):
    """Return the ctypes wrapper for `proc`, with `customisations` applied."""
    from OpenGL import wrapper

    binding = ctypes_callable(proc.__name__, getattr(proc, 'api', None))
    built = wrapper.wrapper(binding)
    for (earlier, __which), earlier_args in customisations.items():
        built = getattr(built, earlier)(*earlier_args)
    return built


def demote_and_call(proc, method, args, keywords):
    """Apply a customisation the C layer lacks, through the ctypes wrapper.

    Some calls change which arguments the entry point takes, and the C layer
    cannot perform them.  Such a call rebuilds the chain's wrapper over the
    ctypes binding.  The customisations the chain absorbed are replayed first,
    so the result is the same as without the C layer.
    """
    return getattr(_replayed(proc, swallowed_for(proc)), method)(
        *args, **keywords
    )


def demoted_callable(proc):
    """Return the callable that replaces an entry point a client demotes.

    Assigning ``errcheck`` or ``argtypes`` moves one entry point to the ctypes
    path.  The replacement must be the function the friendly module would
    have built.  Where the C layer absorbed customisations, the replacement is
    a wrapper that applies them.  ``glShaderSource(shader, string)`` must
    still take two arguments after demotion, while the binding underneath
    takes the four the registry declares.  Only `proc`'s own chain record is
    replayed, so the entry point ``OpenGL.raw`` exports demotes to the
    binding.

    Most entry points have declarative customisations or none, and demote to
    the binding itself.  ``argtypes``, ``DLL`` and the other attributes are
    then read from the binding.
    """
    customisations = swallowed_for(proc)
    if not customisations:
        return ctypes_callable(proc.__name__, getattr(proc, 'api', None))
    return _replayed(proc, customisations)


def array_type_map():
    """Return every ``OpenGL.arrays`` class, keyed by its C table name.

    The C table stores a name per element and looks the names up here at
    configure time, filling its own table in its own order.  The two sides
    share names, never positions.  Shared positions would need a generated
    Python list to match a compiled index.  A checkout whose Python is newer
    than its built extension would then convert with the wrong class and
    raise no error.

    Built from the package instead of a generated list, so any class the
    table names is found if it exists, and reported by name if it does not.
    """
    found = {'ArrayDatatype': arrays.ArrayDatatype}
    for name in dir(arrays):
        if not name.endswith('Array'):
            continue
        value = getattr(arrays, name)
        if hasattr(value, 'asArray'):
            found[name] = value
    return found


#: Mirrors the PYGL_RET_* enum in src/c/pygl.h.
_RET_VOID, _RET_INT, _RET_BYTES, _RET_FLOAT, _RET_OPAQUE, _RET_ADDRESS = range(6)

_RESTYPE_EQUIVALENTS = {
    _RET_VOID: (None,),
    _RET_BYTES: (ctypes.c_char_p,),
    _RET_FLOAT: (ctypes.c_float, ctypes.c_double),
    _RET_ADDRESS: (ctypes.c_void_p,),
}


def restype_matches(kind, value):
    """Return whether an assigned ``restype`` matches the existing conversion.

    Assigning the conversion the C stub already performs changes nothing, so
    it is accepted.  Assigning a different one demotes that entry point to
    ctypes, where any restype behaves as in ctypes.
    """
    return value in _RESTYPE_EQUIVALENTS.get(kind, ())


def lookup_int(pname):
    """Return the element count for an output whose size is a GL query.

    ``_glgets`` records a few pnames, such as GL_COMPRESSED_TEXTURE_FORMATS
    and the pixel-map sizes, whose output length is the result of
    ``glGetIntegerv`` on another pname.
    """
    from OpenGL.GL import glGetIntegerv

    output = ctypes.c_int()
    glGetIntegerv(pname, output)
    return int(output.value)


_signatures = {}


def signature_for(proc):
    """Return an ``inspect.Signature`` for an entry point.

    ``inspect.signature()`` reads ``__text_signature__`` only from the builtin
    callable types.  Entry points therefore return the Signature directly,
    built from the same string the C code carries.

    The string is parsed instead of compiled and run.  pydoc, Sphinx autodoc
    and PyOpenGL's documentation generator call this.  A generated signature
    that fails to parse must not raise a SyntaxError in those tools.

    Cached per ``(api, name)``, because two APIs declare ``glClear`` and the
    name alone does not identify the entry point.
    """
    import inspect

    key = (getattr(proc, 'api', None), proc.__name__)
    signature = _signatures.get(key)
    if signature is None:
        signature = _signatures[key] = inspect.Signature(
            _parameters(proc.__text_signature__)
        )
    return signature


def _parameters(text_signature):
    """Return the parameters a ``__text_signature__`` describes.

    The generator writes only ``$module``, argument names, ``=None`` for an
    output array a caller may supply, and ``/``.  The ``/`` makes the
    parameters positional-only, matching the stubs, which reject keyword
    arguments.  Any other content was not produced by this library and raises
    ValueError.
    """
    import inspect

    inside = text_signature.strip()
    if not (inside.startswith('(') and inside.endswith(')')):
        raise ValueError('not a text signature: %r' % (text_signature,))
    parameters = []
    for part in inside[1:-1].split(','):
        part = part.strip()
        if not part or part in ('/', '$module'):
            # The leading $module is the convention for a bound self, and the
            # entry point takes no such argument.
            continue
        name, _, default = part.partition('=')
        name = name.strip()
        if not name.isidentifier():
            raise ValueError(
                'not a parameter name in %r: %r' % (text_signature, name)
            )
        if default and default.strip() != 'None':
            raise ValueError(
                'not a default this library writes in %r: %r'
                % (text_signature, default.strip())
            )
        parameters.append(
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=None if default else inspect.Parameter.empty,
            )
        )
    return parameters


def raise_debug_error(code, identifier, message, name, arguments=None, api=None):
    """Raise a GL_KHR_debug error report as the exception glGetError gives.

    ``description`` is the driver's own message, instead of a description
    looked up from the code.  ``err`` stays the GL error code, because
    ``GLError`` documents it that way and callers branch on it.  The driver's
    message identifier is a per-driver, per-message number, stored as
    ``debugMessageID``.

    ``baseOperation`` is the entry point instead of its name, as in
    :func:`raise_gl_error`, and the class comes from the same table.  A
    caller gets the same exception whichever mechanism detected the error.
    """
    raised = _error_classes.get(api, error.GLError)(
        err=code,
        description=message,
        baseOperation=_entry_point_or_name(api, name),
        pyArgs=arguments,
        cArgs=arguments,
        cArguments=arguments,
    )
    raised.debugMessageID = identifier
    raise raised


def probe_allowed():
    """Return whether the layer may load EGL or GLX to find the context.

    True only when ``CONTEXT_CHECKING`` is on.  That setting asks for an error
    when no context is current, which requires a definite answer.
    """
    from OpenGL import _configflags

    return bool(_configflags.CONTEXT_CHECKING)


def current_context():
    """Return the current context as an integer handle, or 0.

    The platform layer determines which interface owns the context.  A Linux
    process can hold GLX and EGL contexts at once, and querying the wrong one
    returns no context.

    Converted with :func:`as_pointer`, because :meth:`GetCurrentContext`
    returns each platform's own handle type.  ``int()`` parses any object
    with the buffer protocol as a string of digits, and every ctypes object
    has one.  A pointer would then fail into the 0 below, reporting no current
    context while one is current.
    """
    try:
        # Probing loads EGL and GLX to query each, which costs 26 MB of
        # driver.  A program that only imports PyOpenGL should not pay that,
        # so normally only an already loaded interface is queried.
        # CONTEXT_CHECKING asks for an error when no context is current,
        # which needs the probe, so the flag enables it.
        return as_pointer(
            platform.PLATFORM.GetCurrentContext(probe=probe_allowed())
        )
    except TypeError:  # a platform whose signature predates the argument
        try:
            return as_pointer(platform.PLATFORM.GetCurrentContext())
        except Exception:
            return 0
    except Exception:
        return 0


# ---------------------------------------------------------------- images
#
# The tables that determine an image's length (component counts per format,
# element type per storage type, pixel-store settings per rank) are built at
# import.  OpenGL.images.registerImage extends them at run time, and third
# parties use it for their own formats.  The C layer calls this Python code
# instead of duplicating it, so those registrations keep working.


def _image_dims(rank, d0, d1, d2):
    return (d0, d1, d2)[:rank]


def image_input(name, format, type, rank, d0, d1, d2, value):
    """Return the array for a pixels argument, after setting the transfer mode.

    ``None`` stays ``None``.  An upload with no pixels allocates storage
    without initialising it, which is a common call.
    """
    from OpenGL import images
    from OpenGL.arrays import GL_CONSTANT_TO_ARRAY_TYPE

    images.setupDefaultTransferMode()
    images.rankPacking(rank + 1)
    if value is None:
        return None
    array_type = GL_CONSTANT_TO_ARRAY_TYPE[images.TYPE_TO_ARRAYTYPE.get(type, type)]
    return array_type.asArray(value)


def image_output(name, format, type, rank, d0, d1, d2, value):
    """Return the array a read writes into: the caller's, or a new one."""
    from OpenGL import images
    from OpenGL.arrays import GL_CONSTANT_TO_ARRAY_TYPE

    if value is not None:
        images.setupDefaultTransferMode()
        images.rankPacking(rank + 1)
        array_type = GL_CONSTANT_TO_ARRAY_TYPE[
            images.TYPE_TO_ARRAYTYPE.get(type, type)
        ]
        return array_type.asArray(value)
    return images.SetupPixelRead(format, _image_dims(rank, d0, d1, d2), type)


def image_pointer(array):
    """Return the address of a converted image, or the buffer offset unchanged.

    A `const void *` argument that names a buffer offset has already been
    converted to a ``c_void_p`` holding it, and that value is passed as is.
    Taking its address would pass the driver a pointer to the offset.
    """
    if isinstance(array, ctypes.c_void_p):
        return array
    return arrays.ArrayDatatype.dataPointer(array)


def image_result(array, type):
    """Return the result of a pixel read.

    ``OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING`` converts an unsigned byte image
    to bytes, but only for an image this layer allocated.  A raw pointer
    passed by the caller is returned unchanged.  ``OpenGL.GL.images`` passes
    one when it has allocated the storage itself.  Formatting a pointer as an
    image would read from whatever memory it points at.
    """
    from OpenGL import images

    if isinstance(array, (ctypes._SimpleCData, ctypes._Pointer)):
        return array
    return images.returnFormat(array, type)


def as_typed_array(value, type):
    """Convert to the array type the GL constant names.

    ``glDrawElements`` and the client-side array pointers take the element
    type as an argument, so the type is a value and not a property of the
    entry point.  Any type registered in ``GL_CONSTANT_TO_ARRAY_TYPE`` works
    here.
    """
    from OpenGL.arrays import GL_CONSTANT_TO_ARRAY_TYPE
    from OpenGL.arrays.arraydatatype import buffer_offset

    if value is None:
        return None
    # An integer here is a byte offset into the bound buffer, not one datum to
    # upload; see `OpenGL.arrays.arraydatatype.buffer_offset`.
    offset = buffer_offset(value)
    if offset is not None:
        return offset
    array_type = GL_CONSTANT_TO_ARRAY_TYPE.get(type)
    if array_type is None:
        # No type given, or not an array element type: use the generic path,
        # which accepts anything the handlers accept.
        return arrays.ArrayDatatype.asArray(value)
    return array_type.asArray(value)


#: Where each client-array entry point's pointer is stored against the
#: context.  These are the constants OpenGL/GL/pointers.py uses, so
#: glGetPointerv returns the same values under either implementation.
_POINTER_CONSTANTS = {
    'glVertexPointer': 0x808E,       # GL_VERTEX_ARRAY_POINTER
    'glNormalPointer': 0x808F,       # GL_NORMAL_ARRAY_POINTER
    'glColorPointer': 0x8090,        # GL_COLOR_ARRAY_POINTER
    'glIndexPointer': 0x8091,        # GL_INDEX_ARRAY_POINTER
    'glTexCoordPointer': 0x8092,     # GL_TEXTURE_COORD_ARRAY_POINTER
    'glEdgeFlagPointer': 0x8093,     # GL_EDGE_FLAG_ARRAY_POINTER
    'glInterleavedArrays': 0x8093,   # edge-flag slot, as in pointers.py
}


def retain(name, index, array):
    """Keep an argument alive against the current context.

    GL keeps reading a client-side array after the call that registered it
    returns.  Dropping the reference would cause a crash.
    """
    from OpenGL import contextdata

    constant = _POINTER_CONSTANTS.get(name, name)
    contextdata.setValue(constant, array)
    return array


def string_list(value):
    """Return a list of bytes from one string or a sequence of strings.

    ``glShaderSource`` and ``glTransformFeedbackVaryings`` take either form.
    One string becomes a list of one.  ``OpenGL._string_array`` decides what
    counts as a string, so the result matches the ctypes bindings.
    """
    from OpenGL._string_array import as_bytes

    one = as_bytes(value)
    if one is not None:
        return [one]
    out = []
    for index, item in enumerate(value):
        text = as_bytes(item)
        if text is None:
            raise TypeError(
                'string %d is %s, not a string' % (index, type(item).__name__)
            )
        out.append(text)
    return out
