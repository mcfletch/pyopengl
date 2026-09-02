# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""Backward-compatibility module to provide core-GL constant names"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GL._types')
from OpenGL.arrays._arrayconstants import *
