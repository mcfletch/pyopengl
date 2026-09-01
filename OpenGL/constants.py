"""Backward-compatibility module to provide core-GL constant names"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GL._types')
from OpenGL.arrays._arrayconstants import *
