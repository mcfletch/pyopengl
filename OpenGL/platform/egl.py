"""EGL platform alias

:class:`OpenGL.platform.linux.LinuxPlatform` implements both EGL and GLX.  It
selects between them at runtime by checking which API has a current context.
This module keeps imports of ``EGLPlatform`` from it working.  The ``egl``
and ``wayland`` PYOPENGL_PLATFORM keys select ``LinuxPlatform`` directly.
"""

from OpenGL.platform.linux import LinuxPlatform

# Alias for existing imports; LinuxPlatform supports EGL and GLX.
EGLPlatform = LinuxPlatform
