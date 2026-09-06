"""OpenGL.GLES1.OES.query_matrix -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult

from OpenGL.raw.GLES1._types import *

def glQueryMatrixxOES(mantissa: IntArray | None = None, exponent: IntArray | None = None) -> tuple[IntArrayResult, IntArrayResult]: ...

def glInitQueryMatrixOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
