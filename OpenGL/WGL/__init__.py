# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL._declarations import define as _define
_EXTENSION_NAME = _define(globals(), 'OpenGL.raw.WGL.VERSION.WGL_1_0')

wglUseFontBitmaps = wglUseFontBitmapsW
