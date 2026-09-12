# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
# GLES3's types are GLES2's.  The error checker is next door in `_errors.py`,
# which is where `_declarations` reads every API's from; this module used to
# carry a `_error_function` of its own that nothing read.
from OpenGL.raw.GLES2._types import *
