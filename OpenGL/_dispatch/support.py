"""What the C dispatch layer calls back into Python for.

Everything here is off the hot path: resolving a proc address once per entry
point per context, converting an array the fast path did not match, raising a
GL error, and building the ctypes binding an entry point falls back to when a
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
#: are not GL's and are named by a class of its own, so the class comes from the
#: API whose call failed rather than from one shared default.
_error_classes = {}


def register_error_class(api, errorClass):
    """Remember which exception ``api`` reports its errors with."""
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
    """The address of an entry point *in the current context*, or None.

    This reproduces what ``BasePlatform.constructFunction`` decides, so that an
    entry point the ctypes path would have refused is refused here too.  It runs
    once per entry point per context.

    ``alternates`` names the other extensions that declare the same command,
    comma-joined.  A command is often declared by two -- ``glUniform1i64NV`` by
    both ``GL_NV_gpu_shader5`` and ``GL_AMD_gpu_shader_int64`` -- and a driver
    advertising either has the function, so any one of them is enough.
    """
    from OpenGL import _dispatch, dispatch as _dispatch_api

    # The first resolution is the first moment a context exists, so it is
    # where the layer learns how to ask which one is current, and where a
    # context is offered the cheaper of the two error checks.
    _dispatch.install_context_getter()
    _dispatch_api.offer_debug_output()
    api = _API_NAMES[api_index]
    platform_ = platform.PLATFORM
    is_core = (not extension) or 'VERSION' in extension.split('_')
    if not is_core and not _extension_gate_passes(platform_, extension, alternates):
        return None
    if is_core:
        # The API's own library first, then whatever else this platform says
        # holds its entry points -- on Windows the pixel-format calls and
        # SwapBuffers are GDI rather than OpenGL, and opengl32 does not export
        # them. constructFunction has always fallen back that way; asking the
        # platform means both paths bind the same set rather than one of them
        # quietly finding fewer.
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
    """Whether the extension gate lets this command through.

    The gate reads the context's extension string, and no GL query is legal
    between ``glBegin`` and ``glEnd``.  That is exactly where an immediate-mode
    extension command -- ``glColor3hNV``, ``glPrimitiveRestartNV``,
    ``glMultiTexCoord2fARB`` -- is first called, because a Begin/End block is
    the only place it *may* be called.  Asking anyway answers "no extensions",
    which reports a command the driver does have as undefined and leaves
    GL_INVALID_OPERATION recorded against the block.

    So inside a block the gate stands aside, and the address the windowing
    system hands back decides instead -- a question that does have an answer
    there.  The gate resumes as soon as the block closes, so a command first
    reached outside one is refused exactly as before.
    """
    if error.inside_begin_block():
        return True
    return _any_extension_present(platform_, extension, alternates)


def _any_extension_present(platform_, extension, alternates):
    """Whether the context advertises any extension that declares the command."""
    for name in (extension, *(alternates or '').split(',')):
        if not name:
            continue
        if 'VERSION' in name.split('_'):
            return True  # a core version declares it; no string to check
        if platform_.checkExtension(name):
            return True
    return False


def is_pointer_sized(value):
    """Whether ``value`` is a ctypes scalar whose value *is* an address.

    ``c_void_p`` is the familiar one, and WGL's handles -- ``HDC``, ``HGLRC``,
    ``HPBUFFERARB`` -- are the reason this asks about the declaration rather
    than naming a class.  They are pointer-sized simple types rather than
    pointer classes, because ctypes shares every reference to ``c_void_p`` and
    a shared one would disable the array machinery for everything else.  So
    ``isinstance(handle, c_void_p)`` is False for them while ``.value`` is the
    handle itself.
    """
    return (isinstance(value, ctypes._SimpleCData)
            and getattr(type(value), '_type_', None) == 'P')


def as_pointer(value):
    """The address of anything a client may pass where a pointer is wanted.

    Covers what the ctypes layer accepts today: plain integers, ctypes
    instances, the opaque pointer classes, and the byref result that the ctypes
    array handlers answer ``dataPointer`` with -- which carries its address
    rather than stating it.
    """
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    referent = getattr(value, '_obj', None)
    if referent is not None:
        return ctypes.addressof(referent)
    # A c_void_p's value *is* an address; a c_int's is not.  Reading `.value`
    # off anything that has one turns ctypes.c_int(1234) into address 1234 --
    # so ask what the object is rather than what attributes it happens to
    # carry.  The pointer-sized scalars answer here, and the opaque handle
    # classes are pointer subclasses and answer here too.  Anything that
    # reaches the fallbacks below is answered with the address *of* itself,
    # which for a handle would be a pointer into the interpreter's heap handed
    # to a display driver, with nothing raising to say so.
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


#: Where the handle classes are declared.  It has to be *these* classes rather
#: than freshly built ones: they are what the ctypes bindings name in their
#: argtypes and restypes, so a GLsync built from a different class of the same
#: name is rejected by any entry point still on the ctypes path, and a WGL
#: handle found nowhere would come back as a fabricated pointer class instead
#: of the integer ctypes produces.
_OPAQUE_MODULES = (
    'OpenGL.raw.GL._types',
    'OpenGL.raw.EGL._types',
    'OpenGL.raw.WGL._types',
    'OpenGL.raw.GLX._types',
)


def _declared_class(type_name):
    """The class the bindings declare for ``type_name``, cached.

    A name none of the modules declares gets a freshly built opaque pointer
    class, which is what the ctypes path does with it.
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
    """The object this return type produces, as the ctypes path produces it.

    A pointer class -- GL's ``GLsync``, EGL's ``EGLDisplay`` -- gives an
    instance of itself, which is what a caller comparing two of them relies on.
    A pointer-sized scalar, which is how WGL declares ``HDC`` and its
    neighbours, gives a plain integer, because that is what ctypes converts
    such a result to.  The two implementations are alternatives, so a program
    must not be able to tell from an answer which one it is on.
    """
    cls = _declared_class(type_name)
    if issubclass(cls, ctypes._SimpleCData) and getattr(cls, '_type_', None) == 'P':
        return address
    return ctypes.cast(ctypes.c_void_p(address), cls)


def raise_gl_error(code, name, arguments=None, api=None):
    """The exception a failed call produces.

    It carries the arguments the call was made with, because that is what
    tells a reader which call went wrong -- clients read ``err.pyArgs``, which
    the ctypes path leaves empty.

    ``baseOperation`` is the entry point rather than its name, so that
    ``err.baseOperation.__name__`` keeps working and ``error.py``'s own
    ``format_baseOperation`` takes the branch it was written for.  And
    ``cArguments`` is filled, because ``GLError``'s docstring documents it --
    leaving it empty while putting the same tuple in ``cArgs`` reads as a
    name mix-up rather than a decision.
    """
    raise _error_classes.get(api, error.GLError)(
        err=code,
        baseOperation=_entry_point_or_name(api, name),
        pyArgs=arguments,
        cArgs=arguments,
        cArguments=arguments,
    )


def _entry_point_or_name(api, name):
    """The entry point that failed, or its name where the API is not known.

    ``err.baseOperation.__name__`` is what clients read and what
    ``error.py``'s ``format_baseOperation`` is written for, so the object is
    what an exception carries wherever there is one to carry.
    """
    if api is None:
        return name
    from OpenGL._dispatch import entry_points

    return entry_points.get((api, name)) or name


def register_ctypes_binding(api, name, binding):
    """Remember the ctypes binding a C entry point was installed over."""
    _ctypes_bindings[(api, name)] = binding


def register_module(api, name, module):
    _modules[(api, name)] = module


#: How to build a ctypes binding for an entry point whose declaration has not
#: been run.  Populated by the module finder, which stands in for the files
#: that would have run them.
_ctypes_factories = {}


def register_ctypes_factory(api, name, factory):
    """Remember how to build the ctypes binding an entry point demotes to."""
    _ctypes_factories.setdefault((api, name), factory)


def ctypes_callable(name, api=None):
    """The ctypes binding for an entry point, for demotion and attributes.

    ``api`` identifies which one: ``glClear`` exists in GL and in GLES2 as
    separate bindings resolved from separate libraries, so scanning for the
    first name that matches can hand back the desktop GL function for a GLES2
    entry point -- and on a system serving both, demoting then binds the wrong
    library.  The C passes it; ``None`` keeps the old scan for any caller that
    does not.
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
    """Which module declared this entry point.

    ``api`` for the same reason as :func:`ctypes_callable`: without it,
    ``GLES2.glClear.__module__`` reports the desktop GL module.
    """
    order = (api,) + tuple(_API_NAMES) if api else tuple(_API_NAMES)
    for candidate in order:
        module = _modules.get((candidate, name))
        if module is not None:
            return module
    return 'OpenGL'


#: Customisation calls swallowed because the C already performs them, kept per
#: entry point so that a demotion later in the same chain can replay them.
#: Keyed by (api, name) for the same reason :func:`ctypes_callable` takes an
#: api: two APIs declare ``glClear``, and they are different entry points with
#: different customisations.
_swallowed = {}


def _key_for(proc):
    """``(api, name)`` for an entry point, whichever implementation it is.

    A ``GLProc`` states its api; a ctypes binding reached through the same
    chain does not, and ``None`` there keeps the old name-only behaviour rather
    than inventing an answer.
    """
    return (getattr(proc, 'api', None), proc.__name__)


def swallowed_for(proc):
    """The customisations swallowed for this entry point, as a mapping."""
    return _swallowed.get(_key_for(proc), {})


def record_custom(proc, method, args):
    """Remember a customisation the C already performs.

    A friendly module may build a *derived* function from the same entry point
    -- glVertexPointerd(array) out of glVertexPointer(size, type, stride,
    pointer) -- by continuing the chain with a call that changes the arity.
    That one has to demote, and the wrapper it demotes to needs whatever was
    swallowed before it.
    """
    remembered = _swallowed.setdefault(_key_for(proc), {})
    # Keyed by what it customises, not by call order: a module builds several
    # derived functions from one entry point and restates the same
    # customisation for each, and applying it twice is an error.
    key = (method, args[0] if args else None)
    remembered.setdefault(key, tuple(args))
    return None


def _replayed(proc):
    """The ctypes wrapper for `proc`, carrying what the C swallowed."""
    from OpenGL import wrapper

    binding = ctypes_callable(proc.__name__, getattr(proc, 'api', None))
    built = wrapper.wrapper(binding)
    for (earlier, __which), earlier_args in swallowed_for(proc).items():
        built = getattr(built, earlier)(*earlier_args)
    return built


def demote_and_call(proc, method, args, keywords):
    """A customisation the C does not implement falls back to the wrapper.

    Correctness before speed: a call the C cannot perform -- one that changes
    which arguments the entry point takes -- rebuilds the whole wrapper over
    the ctypes binding, replaying what was swallowed first so the result is
    what it would have been without this layer at all.
    """
    return getattr(_replayed(proc), method)(*args, **keywords)


def demoted_callable(proc):
    """What an entry point becomes when a client demotes it.

    Assigning ``errcheck`` or ``argtypes`` moves one entry point to the ctypes
    path, and what it moves to has to be the function the friendly module
    would have built -- so where customisations were swallowed because the C
    performs them, the wrapper that performs them is what answers.
    ``glShaderSource(shader, string)`` demoted must still take two arguments;
    the binding underneath it takes the four the registry declares.

    Everything else -- the great majority, which the friendly modules describe
    declaratively or not at all -- demotes to the binding itself, as it always
    has, so ``argtypes``, ``DLL`` and the rest are read straight off it.
    """
    if not swallowed_for(proc):
        return ctypes_callable(proc.__name__, getattr(proc, 'api', None))
    return _replayed(proc)


def array_type_map():
    """Every ``OpenGL.arrays`` class, by the name the C element table names it.

    The C table carries a name per element and resolves it here at configure
    time, filling its own table in its own order, so the two sides share a name
    and never a position.  A position would have to be agreed by a generated
    Python list and a compiled index, and a tree whose Python is newer than its
    built extension would then convert with the wrong class and say nothing.

    Built from the package rather than from a generated list, so a class the
    table names is found if it exists at all, and reported by name if it does
    not.
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
    """Whether an assigned ``restype`` is the conversion already in place.

    Assigning the conversion the C stub already performs changes nothing, so it
    is accepted.  Asking for a different one demotes that entry point to
    ctypes, where an arbitrary restype means what it has always meant.
    """
    return value in _RESTYPE_EQUIVALENTS.get(kind, ())


def lookup_int(pname):
    """The element count for an output whose size is itself a GL query.

    ``_glgets`` records a handful of pnames -- GL_COMPRESSED_TEXTURE_FORMATS
    and the pixel-map sizes -- whose output length is whatever a
    ``glGetIntegerv`` of another pname answers.
    """
    from OpenGL.GL import glGetIntegerv

    output = ctypes.c_int()
    glGetIntegerv(pname, output)
    return int(output.value)


_signatures = {}


def signature_for(proc):
    """An ``inspect.Signature`` for an entry point.

    ``inspect.signature()`` reads ``__text_signature__`` only from the builtin
    callable types, so an entry point answers with the Signature itself, built
    from the same string the C carries.

    The string is *read* rather than compiled and run.  This is what pydoc,
    Sphinx autodoc and PyOpenGL's own documentation generator ask for, and a
    generated signature that would not parse should not surface there as a
    SyntaxError raised against whatever they were documenting.

    Cached per ``(api, name)``: two APIs declare ``glClear``, and an entry
    point's signature is not something to hand out by name alone.
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
    """The parameters a ``__text_signature__`` describes.

    The whole vocabulary the generator writes is ``$module``, argument names,
    ``=None`` for an output array a caller may supply, and the ``/`` that makes
    them positional-only -- which is what the stubs implement, since they reject
    a keyword rather than dropping it.  Anything else is not something this
    library produced.
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
    """Turn a GL_KHR_debug error report into the exception glGetError would.

    The driver has already said what went wrong in prose, so ``description`` is
    the driver's own message rather than a code looked up after the fact.
    ``err`` stays the GL error code, because that is what ``GLError`` documents
    it as and what a caller branches on; the driver's message identifier is a
    per-driver, per-message number and rides along as ``debugMessageID`` for
    anyone who wants it.

    ``baseOperation`` is the entry point rather than its name, as it is in
    :func:`raise_gl_error`: which mechanism noticed an error is not something a
    caller reading the exception should have to know.  The class comes from the
    same table for the same reason -- one call cannot raise two classes
    depending on which mechanism saw it.
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
    """Whether the layer may load EGL/GLX in order to ask about contexts.

    Only where the caller has asked to be told about a missing context, which
    is the one case where "do not know" is not an acceptable answer.
    """
    from OpenGL import _configflags

    return bool(_configflags.CONTEXT_CHECKING)


def current_context():
    """Which context is current, as an integer handle.

    The platform layer is the only thing that knows which interface owns it:
    a Linux process can hold GLX and EGL contexts at once, and asking the
    wrong one answers "none".

    Read through :func:`as_pointer`, because :meth:`GetCurrentContext` is
    documented for the opaque pointer a platform names a context by and every
    platform answers in the shape its own API declares.  ``int()`` would not
    do: handed anything offering the buffer protocol -- which every ctypes
    object does -- it reads the bytes as a string of digits, so a pointer
    falls to the 0 below, which says no context is current while one is.
    """
    try:
        # Probing means loading EGL and GLX to ask each of them, and loading
        # them costs 26 MB of driver.  A program that merely imports PyOpenGL
        # should not pay that, so the question is normally answered only from
        # an interface already loaded -- but CONTEXT_CHECKING is a caller
        # asking to be told when no context is current, and that answer cannot
        # be had without asking.  The flag is what buys the probe.
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
# The tables that decide an image's length -- component counts per format,
# element type per storage type, the pixel-store settings per rank -- are
# built at import and extended at run time by OpenGL.images.registerImage,
# which third parties use for their own formats.  Reusing that code rather
# than restating it in C is what keeps those registrations working.


def _image_dims(rank, d0, d1, d2):
    return (d0, d1, d2)[:rank]


def image_input(name, format, type, rank, d0, d1, d2, value):
    """The array a pixels argument becomes, with the transfer mode set.

    ``None`` stays ``None``: an upload with no pixels allocates storage
    without initialising it, which is a real and common call.
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
    """Where a read puts its result: the caller's array, or a new one."""
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
    """The address of a converted image, or the offset it already is.

    A `const void *` argument that named a buffer offset has already been
    turned into the ``c_void_p`` holding it, and that is the value to pass:
    taking its address would hand the driver a pointer to the offset.
    """
    if isinstance(array, ctypes.c_void_p):
        return array
    return arrays.ArrayDatatype.dataPointer(array)


def image_result(array, type):
    """What a read hands back.

    ``OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING`` turns an unsigned byte image into
    bytes, which is what it does today -- but only for an image this layer
    allocated.  A caller who passed a raw pointer, as ``OpenGL.GL.images``
    does when it has already made the storage itself, gets it back unchanged:
    formatting a pointer as an image reads from wherever it happens to point.
    """
    from OpenGL import images

    if isinstance(array, (ctypes._SimpleCData, ctypes._Pointer)):
        return array
    return images.returnFormat(array, type)


def as_typed_array(value, type):
    """Convert to the array type the GL constant names.

    ``glDrawElements`` and the client-side array pointers say what their data
    is made of in an argument rather than in their signature, so the element
    type is a value rather than a property of the entry point.  A type
    registered in ``GL_CONSTANT_TO_ARRAY_TYPE`` works here without this
    knowing about it.
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
        # No type named, or one that is not an array element type: hand it to
        # the generic path, which accepts whatever the handlers accept.
        return arrays.ArrayDatatype.asArray(value)
    return array_type.asArray(value)


#: Where each client-array entry point's pointer is stored against the
#: context.  These are the constants OpenGL/GL/pointers.py uses, so a program
#: that reads them back with glGetPointerv sees what it always has.
_POINTER_CONSTANTS = {
    'glVertexPointer': 0x808E,       # GL_VERTEX_ARRAY_POINTER
    'glNormalPointer': 0x808F,       # GL_NORMAL_ARRAY_POINTER
    'glColorPointer': 0x8090,        # GL_COLOR_ARRAY_POINTER
    'glIndexPointer': 0x8091,        # GL_INDEX_ARRAY_POINTER
    'glTexCoordPointer': 0x8092,     # GL_TEXTURE_COORD_ARRAY_POINTER
    'glEdgeFlagPointer': 0x8093,     # GL_EDGE_FLAG_ARRAY_POINTER
    'glInterleavedArrays': 0x8093,   # shares the edge-flag slot, as today
}


def retain(name, index, array):
    """Keep an argument alive against the current context.

    The GL goes on reading a client-side array after the call that registered
    it returns, so dropping the reference is a crash rather than a leak.
    """
    from OpenGL import contextdata

    constant = _POINTER_CONSTANTS.get(name, name)
    contextdata.setValue(constant, array)
    return array


def string_list(value):
    """A list of bytes, from one string or a sequence of them.

    ``glShaderSource`` and ``glTransformFeedbackVaryings`` both take either
    form, and a caller who passes one string means a list of one.  What counts
    as a string is ``OpenGL._string_array``'s to say, so that this answers as
    the ctypes bindings do.
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
