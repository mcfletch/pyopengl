"""OpenGL.GL.NV.explicit_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_INT_SAMPLER_RENDERBUFFER_NV: int
GL_MAX_SAMPLE_MASK_WORDS_NV: int
GL_SAMPLER_RENDERBUFFER_NV: int
GL_SAMPLE_MASK_NV: int
GL_SAMPLE_MASK_VALUE_NV: int
GL_SAMPLE_POSITION_NV: int
GL_TEXTURE_BINDING_RENDERBUFFER_NV: int
GL_TEXTURE_RENDERBUFFER_DATA_STORE_BINDING_NV: int
GL_TEXTURE_RENDERBUFFER_NV: int
GL_UNSIGNED_INT_SAMPLER_RENDERBUFFER_NV: int

def glGetMultisamplefvNV(pname: int, index: int, val: FloatArray | None = None) -> FloatArrayResult: ...
def glSampleMaskIndexedNV(index: int, mask: int) -> None: ...
def glTexRenderbufferNV(target: int, renderbuffer: int) -> None: ...

def glInitExplicitMultisampleNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
