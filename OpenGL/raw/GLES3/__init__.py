# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.raw.GLES3._types import *
from OpenGL.GLES3.VERSION.GLES3_3_0 import *
