"""Build-time generator for PyOpenGL's C dispatch layer.

Reads the vendored Khronos registry plus the annotation data file and emits the
C implementation of the entry points, the ``.pyi`` stubs and the command
tables.  See ``plans/C-DISPATCH.md`` for the design this implements.

Nothing here is imported at run time; it runs from ``src/regenerate_c.py``.
"""

__all__ = ['ctypes_model']
