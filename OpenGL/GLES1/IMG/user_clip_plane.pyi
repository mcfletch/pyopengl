"""OpenGL.GLES1.IMG.user_clip_plane -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, IntArray

from OpenGL.raw.GLES1._types import *

GL_CLIP_PLANE0_IMG: int
GL_CLIP_PLANE1_IMG: int
GL_CLIP_PLANE2_IMG: int
GL_CLIP_PLANE3_IMG: int
GL_CLIP_PLANE4_IMG: int
GL_CLIP_PLANE5_IMG: int
GL_MAX_CLIP_PLANES_IMG: int

def glClipPlanefIMG(p: int, eqn: FloatArray) -> None: ...
def glClipPlanexIMG(p: int, eqn: IntArray) -> None: ...

def glInitUserClipPlaneIMG() -> bool: ...

def __getattr__(name: str) -> Any: ...
