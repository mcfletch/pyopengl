"""OpenGL.GLES2.NV.internalformat_sample_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GLES2._types import *

GL_CONFORMANT_NV: int
GL_MULTISAMPLES_NV: int
GL_RENDERBUFFER: int
GL_SUPERSAMPLE_SCALE_X_NV: int
GL_SUPERSAMPLE_SCALE_Y_NV: int
GL_TEXTURE_2D_MULTISAMPLE: int
GL_TEXTURE_2D_MULTISAMPLE_ARRAY: int

def glGetInternalformatSampleivNV(target: int, internalformat: int, samples: int, pname: int, count: int, params: IntArray) -> None: ...

def glInitInternalformatSampleQueryNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
