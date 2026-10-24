"""Linux (and BSD) platform supporting either GLX or EGL at runtime

The session type does not determine which context API a program uses.  GLUT
running under XWayland creates a GLX context even though ``WAYLAND_DISPLAY``
is set.  A GLFW window can create either a GLX or an EGL context in any
session.

PyOpenGL must determine which context API (GLX or EGL) owns the current
context.  GLX and EGL keep independent per-thread current-context state, so
both can be queried at runtime.  This platform loads both interfaces where
available and queries each for a current context.

The ``linux``, ``glx``, ``egl``, ``x11``, ``wayland`` and ``xwayland``
platform keys all select this class.  WGL (win32) and CGL (darwin) each have
a single API and use their own platforms.
"""

import ctypes, ctypes.util
from OpenGL.platform import baseplatform, ctypesloader


class LinuxPlatform(baseplatform.BasePlatform):
    """Linux/BSD implementation supporting GLX and/or EGL, chosen at runtime

    The library loaders below cover both GLX and EGL.  Each library is loaded
    on first use.  A missing interface (no libGLX on an EGL-only system, or no
    libEGL on a GLX-only system) yields ``None`` rather than raising, and the
    runtime query skips it.
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
        """The address of extension procedure ``name``, from the owning API

        An ``egl*`` name is resolved first by ``eglGetProcAddress``, and a
        ``glX*`` name first by ``glXGetProcAddressARB``.  Both APIs resolve a
        core ``gl*`` name, so it is resolved by the API that owns the current
        context.  With no current context, GLX is tried first, as the desktop
        default.
        """
        prefix = name[:3]
        if isinstance(prefix, bytes):
            prefix = prefix.decode('ascii', 'replace')
        if prefix == 'egl':
            # The prefix decides, regardless of the current context.  GLVND's
            # glXGetProcAddressARB returns a non-null dispatch stub for any
            # name, including an ``egl*`` one.  That pointer can be called
            # without error but is not the function's entry point.  An EGL
            # client extension resolved through GLX (such as the
            # device-enumeration functions, called before any context exists)
            # then returns failure with EGL_SUCCESS set.
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

    def currentContextAddress(self, probe=True):
        """The address of the get-current-context function of the active API.

        The active API (EGL or GLX) is found at runtime, so the C dispatch
        layer receives this address instead of a fixed symbol.

        Finding the active API queries both, and each query loads its driver
        (26 MB on an NVIDIA machine).  Before an application makes a context
        current there is nothing to find.  With ``probe`` false, only an
        interface already loaded into the process is considered.  ``None``
        then means "not known yet; call again later".
        """
        if self._active_api is None:
            if not probe:
                return None
            self.GetCurrentContext()
        if self._active_api == 'egl':
            function = self._eglGetCurrentContext
        else:
            function = self._glXGetCurrentContext
        if function is None:
            return None
        return ctypes.cast(function, ctypes.c_void_p).value

    #: The two interfaces that can own a context here, as (lazy property name,
    #: value stored in ``_active_api`` when it reports a current context).
    _CONTEXT_APIS = (('_eglGetCurrentContext', 'egl'), ('_glXGetCurrentContext', 'glx'))

    def GetCurrentContext(self, probe=True):
        """Retrieve an opaque pointer for the current context

        Probes EGL first, then GLX.  Both queries read independent per-thread
        driver state and are safe to call even when the corresponding interface
        has no current context (they return a null pointer).  The API that
        returns a live context is stored, so extension lookups use the
        matching get-proc-address function.

        Probing loads both libraries.  On an NVIDIA machine, loading GLX loads
        26 MB of driver.  With ``probe`` false, only an interface already
        loaded into this process is queried, at no load cost.  The result is
        ``None`` until an interface is loaded.  Any program with a current
        context has already loaded the interface it uses.
        """
        if not probe:
            for attribute, api in self._CONTEXT_APIS:
                # The resolved lazy_property, if it has ever been resolved.
                fn = self.__dict__.get(attribute)
                if fn is None:
                    continue
                context = fn()
                if context:
                    self._active_api = api
                    return context
            return None
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

    def releaseCurrentContext(self):
        """Release this thread's current EGL or GLX context; True if released

        See
        :meth:`OpenGL.platform.baseplatform.BasePlatform.releaseCurrentContext`
        for why a program using two GL binding APIs needs this.  EGL and GLX
        do not track each other.  Each refuses to make a context current while
        the other's context is current.  GLX refuses with an X error that ends
        the process.

        Both APIs are checked, because either may hold the thread.  The checks
        cost little compared with creating a context.
        """
        released = False
        if self._releaseEGL():
            released = True
        if self._releaseGLX():
            released = True
        return released

    def _releaseEGL(self):
        """Release a current EGL context; True if one was current"""
        fn = self._eglGetCurrentContext
        if fn is None or not fn():
            return False
        try:
            from OpenGL import EGL
        except ImportError:                 # pragma: no cover - no EGL here
            return False
        display = EGL.eglGetCurrentDisplay()
        if not display:
            return False
        EGL.eglMakeCurrent(display, EGL.EGL_NO_SURFACE, EGL.EGL_NO_SURFACE,
                           EGL.EGL_NO_CONTEXT)
        return True

    def _releaseGLX(self):
        """Release a current GLX context; True if one was current"""
        fn = self._glXGetCurrentContext
        if fn is None or not fn():
            return False
        try:
            from OpenGL import GLX
        except ImportError:                 # pragma: no cover - no GLX here
            return False
        display = GLX.glXGetCurrentDisplay()
        if not display:
            return False
        GLX.glXMakeCurrent(display, 0, None)
        return True

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
