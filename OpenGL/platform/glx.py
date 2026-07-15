"""GLX (X11) platform -- compatibility shim

The GLX and EGL platforms have been merged into
:class:`OpenGL.platform.unix.UnixPlatform`, which supports either interface and
selects between them at runtime by probing for the current context.  This
module is retained so that existing imports (and the ``glx`` PYOPENGL_PLATFORM
key) keep working.
"""

from OpenGL.platform.unix import UnixPlatform

# Backwards-compatible alias; GLXPlatform now supports GLX *or* EGL.
GLXPlatform = UnixPlatform
