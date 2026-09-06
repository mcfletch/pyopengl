"""OpenGL.GLES2.OES.texture_storage_multisample_2d_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY_OES: int
GL_SAMPLER_2D_MULTISAMPLE_ARRAY_OES: int
GL_TEXTURE_2D_MULTISAMPLE_ARRAY_OES: int
GL_TEXTURE_BINDING_2D_MULTISAMPLE_ARRAY_OES: int
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY_OES: int

def glTexStorage3DMultisampleOES(target: int, samples: int, internalformat: int, width: int, height: int, depth: int, fixedsamplelocations: bool) -> None: ...

def glInitTextureStorageMultisample2DArrayOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
