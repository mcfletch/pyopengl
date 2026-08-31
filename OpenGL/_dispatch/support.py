"""What the C dispatch layer calls back into Python for.

Everything here is off the hot path: resolving a proc address once per entry
point per context, converting an array the fast path did not match, raising a
GL error, and building the ctypes binding an entry point falls back to when a
client demotes it.
"""

import ctypes

from OpenGL import arrays, error, platform
from OpenGL._bytes import as_8_bit

__all__ = [
    'resolve',
    'as_pointer',
    'opaque',
    'raise_gl_error',
    'ctypes_callable',
    'module_for',
    'array_type_list',
]

#: (api, name) -> the ctypes binding, recorded when the C entry point is
#: installed over it.  Demotion and the ``argtypes``/``restype``/``DLL``
#: attributes read from here.
_ctypes_bindings = {}
_modules = {}

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


def resolve(name, extension, _unused, api_index):
    """The address of an entry point *in the current context*, or None.

    This reproduces what ``BasePlatform.constructFunction`` decides, so that an
    entry point the ctypes path would have refused is refused here too.  It runs
    once per entry point per context.
    """
    api = _API_NAMES[api_index]
    platform_ = platform.PLATFORM
    is_core = (not extension) or 'VERSION' in extension.split('_')
    if not is_core and not platform_.checkExtension(extension):
        return None
    dll = _dll_for(api)
    if is_core and dll is not None:
        try:
            function = getattr(dll, name)
        except AttributeError:
            pass
        else:
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
    for attribute in ('value', '_as_parameter_'):
        inner = getattr(value, attribute, None)
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
        raise TypeError('cannot use %r as a pointer' % (type(value).__name__,))


_opaque_classes = {}


#: Where the opaque pointer classes are declared.  It has to be *these*
#: classes rather than freshly built ones: they are what the ctypes bindings
#: name in their argtypes, so a GLsync built from a different class of the same
#: name is rejected by any entry point still on the ctypes path.
_OPAQUE_MODULES = ('OpenGL.raw.GL._types', 'OpenGL.raw.EGL._types')


def opaque(address, type_name):
    """Rebuild the opaque pointer object this return type produces today."""
    import importlib

    cls = _opaque_classes.get(type_name)
    if cls is None:
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
    return ctypes.cast(ctypes.c_void_p(address), cls)


def raise_gl_error(code, name):
    raise error.GLError(err=code, baseOperation=name)


def register_ctypes_binding(api, name, binding):
    """Remember the ctypes binding a C entry point was installed over."""
    _ctypes_bindings[(api, name)] = binding


def register_module(api, name, module):
    _modules[(api, name)] = module


def ctypes_callable(name):
    """The ctypes binding for an entry point, for demotion and attributes."""
    for api in _API_NAMES:
        binding = _ctypes_bindings.get((api, name))
        if binding is not None:
            return binding
    raise AttributeError('no ctypes binding recorded for %s' % (name,))


def module_for(name):
    for api in _API_NAMES:
        module = _modules.get((api, name))
        if module is not None:
            return module
    return 'OpenGL'


def demote_and_call(proc, method, args, keywords):
    """A customisation the C does not implement falls back to the wrapper.

    Correctness before speed: if the generator ever emits an entry point whose
    friendly behaviour it does not fully implement, the customisation call
    lands here and the ctypes wrapper takes over for that one function.
    """
    from OpenGL import wrapper

    binding = ctypes_callable(proc.__name__)
    return getattr(wrapper.wrapper(binding), method)(*args, **keywords)


def array_type_list(names):
    """The ``OpenGL.arrays`` classes, in the order the element table indexes."""
    return [getattr(arrays, name) for name in names]


#: Mirrors the PYGL_RET_* enum in src/c/pygl.h.
_RET_VOID, _RET_INT, _RET_BYTES, _RET_FLOAT, _RET_OPAQUE = range(5)

_RESTYPE_EQUIVALENTS = {
    _RET_VOID: (None,),
    _RET_BYTES: (ctypes.c_char_p,),
    _RET_FLOAT: (ctypes.c_float, ctypes.c_double),
}


def restype_matches(kind, value):
    """Whether an assigned ``restype`` is the conversion already in place.

    Assigning the conversion the C stub already performs changes nothing, so it
    is accepted.  Asking for a different one demotes that entry point to
    ctypes, where an arbitrary restype means what it has always meant.
    """
    return value in _RESTYPE_EQUIVALENTS.get(kind, ())
