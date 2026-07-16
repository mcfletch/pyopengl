"""EGL platform -- compatibility shim

The GLX and EGL platforms have been merged into
:class:`OpenGL.platform.linux.LinuxPlatform`, which supports either interface
and selects between them at runtime by probing for the current context.  This
module is retained so that existing imports (and the ``egl``/``wayland``
PYOPENGL_PLATFORM keys) keep working.
"""

from OpenGL.platform.linux import LinuxPlatform

# Backwards-compatible alias; EGLPlatform now supports EGL *or* GLX.
EGLPlatform = LinuxPlatform
