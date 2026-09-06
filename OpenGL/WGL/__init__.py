# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL._declarations import define as _define
_EXTENSION_NAME = _define(globals(), 'OpenGL.raw.WGL.VERSION.WGL_1_0')

wglUseFontBitmaps = wglUseFontBitmapsW

# Rendering with no window on screen.  Bound here so that a caller who has
# imported the package can reach it as ``WGL.offscreen.headless_context()``;
# the module imports ctypes and nothing else at import time, and loads the
# Win32 entry points and the WGL extensions it needs on the first call.
from OpenGL.WGL import offscreen      # noqa: E402,F401 -- after the declarations
