"""Linux (and BSD) platform supporting either GLX or EGL at runtime

Historically PyOpenGL shipped two separate platforms here: ``glx`` (desktop
X11/GLX) and ``egl`` (embedded / Wayland / headless).  The choice was made
*once*, at import time, from environment guesses (e.g. the presence of
``WAYLAND_DISPLAY``).  That guess is frequently wrong: a GLX toolkit such as
GLUT run under XWayland creates a *GLX* context even though ``WAYLAND_DISPLAY``
is set, and a GLFW window can create either a GLX or an EGL context regardless
of the session type.

The toolkit is invisible and irrelevant to us; the only thing we actually need
to know is which *context API* (GLX or EGL) owns the current context, and that
is discoverable at runtime because GLX and EGL keep independent per-thread
current-context state.  This platform therefore loads both interfaces (when
available) and *probes* for the live context rather than committing to one API
up front.

WGL (win32) and AGL/CGL (darwin) are single-API platforms and are left as-is.
"""

import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader


class LinuxPlatform(baseplatform.BasePlatform):
    """Linux/BSD implementation supporting GLX and/or EGL, chosen at runtime

    The library loaders below are the union of the old GLXPlatform and
    EGLPlatform loaders.  Everything is loaded lazily and tolerantly: a missing
    interface (no libGLX on a pure-EGL box, or no libEGL on a legacy GLX box)
    yields ``None`` rather than raising, so the runtime probe can simply skip it.
    """

    # Which context API served the most recent GetCurrentContext()/extension
    # lookup.  Used to route getExtensionProcedure to the matching
    # get-proc-address function.  'egl', 'glx', or None (nothing probed yet).
    _active_api = None

    # On Linux (and most GLX platforms) we have to load GL/GLU with the
    # "global" flag so that GLUT can resolve its references to GL/GLU functions.
    @baseplatform.lazy_property
    def GL(self):
        for name in ('OpenGL', 'GL'):
            try:
                lib = ctypesloader.loadLibrary(
                    ctypes.cdll, name, mode=ctypes.RTLD_GLOBAL
                )
            except OSError:
                lib = None
            if lib:
                return lib
        # Fall back to a GLES library if a full GL library is unavailable
        # (embedded / EGL-only systems).
        return self.GLES2 or self.GLES1

    @baseplatform.lazy_property
    def GLU(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, "GLU", mode=ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None

    @baseplatform.lazy_property
    def GLUT(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, "glut", mode=ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None

    @baseplatform.lazy_property
    def GLX(self):
        """The GLX interface, or None if this system has no GLX"""
        try:
            for name in ('GLX', 'OpenGL', 'GL'):
                try:
                    lib = ctypesloader.loadLibrary(
                        ctypes.cdll, name, mode=ctypes.RTLD_GLOBAL
                    )
                except OSError:
                    continue
                if lib and getattr(lib, 'glXCreateContext', None):
                    return lib
        except OSError:
            pass
        return None

    @baseplatform.lazy_property
    def EGL(self):
        """The EGL interface, or None if this system has no EGL"""
        # The raspberry pi crashes trying to load EGL because the EGL library
        # requires a structure from GLES2 without linking to that library:
        #   https://github.com/raspberrypi/firmware/issues/110
        import os
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                info = f.read()
            if 'BCM2708' in info or 'BCM2709' in info:
                if not self.GLES2:
                    return None
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, 'EGL', mode=ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None

    @baseplatform.lazy_property
    def GLES1(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, "GLESv1_CM", mode=ctypes.RTLD_GLOBAL  # ick
            )
        except OSError:
            return None

    @baseplatform.lazy_property
    def GLES2(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, "GLESv2", mode=ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None

    @baseplatform.lazy_property
    def GLES3(self):
        # implementers guide says to use the same name for the DLL
        return self.GLES2

    @baseplatform.lazy_property
    def GLE(self):
        try:
            return ctypesloader.loadLibrary(
                ctypes.cdll, "gle", mode=ctypes.RTLD_GLOBAL
            )
        except OSError:
            return None

    DEFAULT_FUNCTION_TYPE = staticmethod(ctypes.CFUNCTYPE)

    # -- get-proc-address functions for each interface ----------------------

    @baseplatform.lazy_property
    def glXGetProcAddressARB(self):
        glx = self.GLX
        if glx is None:
            return None
        try:
            base = glx.glXGetProcAddressARB
        except AttributeError:
            return None
        base.restype = ctypes.c_void_p
        return base

    @baseplatform.lazy_property
    def eglGetProcAddress(self):
        egl = self.EGL
        if egl is None:
            return None
        try:
            base = egl.eglGetProcAddress
        except AttributeError:
            return None
        base.restype = ctypes.c_void_p
        return base

    def getExtensionProcedure(self, name):
        """Resolve an extension procedure via the interface that owns it

        An ``egl*`` or ``glX*`` name names its own interface, so it is resolved
        by that interface's get-proc-address and never the other's: GLVND's
        glXGetProcAddressARB manufactures a non-null dispatch stub for *any*
        name, so asking it for an ``egl*`` function (as happened when no context
        was current) returns a pointer that is not the real entry point and
        whose call silently fails.  A core ``gl*`` name is served by both, so it
        follows whichever API currently owns a context, falling back -- when
        nothing is current -- to GLX (the historical desktop default).
        """
        prefix = name[:3]
        if isinstance(prefix, bytes):
            prefix = prefix.decode('ascii', 'replace')
        if prefix == 'egl':
            order = (self.eglGetProcAddress, self.glXGetProcAddressARB)
        elif prefix == 'glX':
            order = (self.glXGetProcAddressARB, self.eglGetProcAddress)
        else:
            api = self._active_api
            if api is None:
                # Probe so a live context selects the matching interface.
                self.GetCurrentContext()
                api = self._active_api
            if api == 'egl':
                order = (self.eglGetProcAddress, self.glXGetProcAddressARB)
            else:
                order = (self.glXGetProcAddressARB, self.eglGetProcAddress)
        for getProcAddress in order:
            if getProcAddress is not None:
                return getProcAddress(name)
        raise RuntimeError(
            "Unable to find a GLX or EGL get-proc-address function"
        )

    # -- current-context probing --------------------------------------------

    @baseplatform.lazy_property
    def _eglGetCurrentContext(self):
        egl = self.EGL
        if egl is None:
            return None
        try:
            fn = egl.eglGetCurrentContext
        except AttributeError:
            return None
        fn.restype = ctypes.c_void_p
        return fn

    @baseplatform.lazy_property
    def _glXGetCurrentContext(self):
        glx = self.GLX
        if glx is None:
            return None
        try:
            fn = glx.glXGetCurrentContext
        except AttributeError:
            return None
        fn.restype = ctypes.c_void_p
        return fn

    def GetCurrentContext(self):
        """Retrieve an opaque pointer for the current context

        Probes EGL first, then GLX.  Both queries read independent per-thread
        driver state and are safe to call even when the corresponding interface
        has no current context (they return a null pointer).  The API that
        returns a live context is remembered so extension lookups route to the
        matching get-proc-address function.
        """
        fn = self._eglGetCurrentContext
        if fn is not None:
            context = fn()
            if context:
                self._active_api = 'egl'
                return context
        fn = self._glXGetCurrentContext
        if fn is not None:
            context = fn()
            if context:
                self._active_api = 'glx'
                return context
        return None

    def getGLUTFontPointer(self, constant):
        """Platform specific function to retrieve a GLUT font pointer

        GLUTAPI void *glutBitmap9By15;
        #define GLUT_BITMAP_9_BY_15		(&glutBitmap9By15)

        Key here is that we want the addressof the pointer in the DLL,
        not the pointer in the DLL.  That is, our pointer is to the
        pointer defined in the DLL, we don't want the *value* stored in
        that pointer.
        """
        name = [x.title() for x in constant.split("_")[1:]]
        internal = "glut" + "".join([x.title() for x in name])
        pointer = ctypes.c_void_p.in_dll(self.GLUT, internal)
        return ctypes.c_void_p(ctypes.addressof(pointer))

    @baseplatform.lazy_property
    def glGetError(self):
        return self.GL.glGetError

    def install(self, namespace):
        """Install, working around SDL not recognising wayland by default"""
        result = super(LinuxPlatform, self).install(namespace)
        import os
        if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
            if not os.environ.get('SDL_VIDEODRIVER'):
                os.environ['SDL_VIDEODRIVER'] = 'wayland'
        return result
