"""OpenGL.GL.NV.draw_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

def glDrawTextureNV(texture: int, sampler: int, x0: float, y0: float, x1: float, y1: float, z: float, s0: float, t0: float, s1: float, t1: float) -> None: ...

def glInitDrawTextureNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
