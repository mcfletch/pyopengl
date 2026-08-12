# EGL extension functions silently fail when no GL context is current

## Summary

Calling an `egl*EXT` client extension function (e.g. `eglQueryDevicesEXT`)
before any GL context exists returns `EGL_FALSE` with `eglGetError() ==
EGL_SUCCESS`, and no devices are enumerated. The function pointer PyOpenGL
binds is a non-null but wrong entry point, so the call marshals correctly and
returns garbage.

## Impact

The EGL device-enumeration / device-platform family
(`EGL_EXT_device_enumeration`, `EGL_EXT_device_query`,
`EGL_EXT_platform_device`) is unusable through PyOpenGL on a GLVND system.
These are precisely the functions used *before* a context exists — to pick
which GPU to create the context on — so the broken path is the normal path.
`tests/check_egl_device_enumeration.py` reaches it and silently logs "Unable
to query devices".

## Root cause

`OpenGL/platform/unix.py:getExtensionProcedure` chooses between
`eglGetProcAddress` and `glXGetProcAddressARB` by which context API is current.
When nothing is current (`_active_api is None` and the probe finds no context)
it falls back to **GLX first**:

```python
if api == 'egl':
    order = (self.eglGetProcAddress, self.glXGetProcAddressARB)
else:  # includes api is None
    order = (self.glXGetProcAddressARB, self.eglGetProcAddress)
```

GLVND's `glXGetProcAddressARB` manufactures a non-null dispatch stub for *any*
name, including an `egl*` one, rather than returning NULL. So the `egl*`
function is resolved to a GLX trampoline that is not its real entry point.

Observed on this machine (NVIDIA + Intel UHD 630, GLVND):

```
glXGetProcAddressARB("eglQueryDevicesEXT") = 0x...672300   # non-null, WRONG
eglGetProcAddress("eglQueryDevicesEXT")    = 0x...470de0   # correct
```

Calling the first returns `EGL_FALSE` (no error set); calling the second
enumerates the three devices correctly.

The context-based ordering is right for core `gl*` functions (both resolvers
serve them, and the one owning the current context is the correct choice), but
an `egl*` or `glX*` name names its own interface unambiguously and must be
resolved by that interface's get-proc-address — never the other's.

## Fix

Route by function-name prefix first: `egl*` → `eglGetProcAddress`, `glX*` →
`glXGetProcAddressARB`. Only names both interfaces serve (core `gl*`) fall
through to the existing context-based ordering. See
`OpenGL/platform/unix.py` and
`tests/test_getextensionprocedure_routing.py`.
