"""OpenGL.GL.ARB.texture_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_INT_SAMPLER_2D_MULTISAMPLE: int
GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: int
GL_MAX_COLOR_TEXTURE_SAMPLES: int
GL_MAX_DEPTH_TEXTURE_SAMPLES: int
GL_MAX_INTEGER_SAMPLES: int
GL_MAX_SAMPLE_MASK_WORDS: int
GL_PROXY_TEXTURE_2D_MULTISAMPLE: int
GL_PROXY_TEXTURE_2D_MULTISAMPLE_ARRAY: int
GL_SAMPLER_2D_MULTISAMPLE: int
GL_SAMPLER_2D_MULTISAMPLE_ARRAY: int
GL_SAMPLE_MASK: int
GL_SAMPLE_MASK_VALUE: int
GL_SAMPLE_POSITION: int
GL_TEXTURE_2D_MULTISAMPLE: int
GL_TEXTURE_2D_MULTISAMPLE_ARRAY: int
GL_TEXTURE_BINDING_2D_MULTISAMPLE: int
GL_TEXTURE_BINDING_2D_MULTISAMPLE_ARRAY: int
GL_TEXTURE_FIXED_SAMPLE_LOCATIONS: int
GL_TEXTURE_SAMPLES: int
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: int
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: int

def glGetMultisamplefv(pname: int, index: int, val: FloatArray | None = None) -> FloatArrayResult: ...
def glSampleMaski(maskNumber: int, mask: int) -> None: ...
def glTexImage2DMultisample(target: int, samples: int, internalformat: int, width: int, height: int, fixedsamplelocations: int) -> None: ...
def glTexImage3DMultisample(target: int, samples: int, internalformat: int, width: int, height: int, depth: int, fixedsamplelocations: int) -> None: ...

def glInitTextureMultisampleARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
