# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL._declarations import define as _define
_EXTENSION_NAME = _define(globals(), 'OpenGL.raw.WGL.VERSION.WGL_1_0')

wglUseFontBitmaps = wglUseFontBitmapsW

# Offscreen rendering.  Imported here so a caller can use
# ``WGL.offscreen.headless_context()`` after importing the package.  At
# import time the module imports only the standard library (contextlib,
# ctypes and sys).  It loads the Win32 entry
# points and WGL extensions on the first call.
from OpenGL.WGL import offscreen  # after the declarations
