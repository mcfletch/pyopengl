"""GLX (X11) platform alias

:class:`OpenGL.platform.linux.LinuxPlatform` implements both GLX and EGL.  It
selects between them at runtime by checking which API has a current context.
This module keeps imports of ``GLXPlatform`` from it working.  The ``glx``
PYOPENGL_PLATFORM key selects ``LinuxPlatform`` directly.
"""

from OpenGL.platform.linux import LinuxPlatform

# Alias for existing imports; LinuxPlatform supports GLX and EGL.
GLXPlatform = LinuxPlatform
