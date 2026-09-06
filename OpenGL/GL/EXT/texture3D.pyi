"""OpenGL.GL.EXT.texture3D -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_MAX_3D_TEXTURE_SIZE_EXT: int
GL_PACK_IMAGE_HEIGHT_EXT: int
GL_PACK_SKIP_IMAGES_EXT: int
GL_PROXY_TEXTURE_3D_EXT: int
GL_TEXTURE_3D_EXT: int
GL_TEXTURE_DEPTH_EXT: int
GL_TEXTURE_WRAP_R_EXT: int
GL_UNPACK_IMAGE_HEIGHT_EXT: int
GL_UNPACK_SKIP_IMAGES_EXT: int

def glTexImage3DEXT(target: int, level: int, internalformat: int, width: int, height: int, depth: int, border: int, format: int, type: int, pixels: AnyArray) -> None: ...
def glTexSubImage3DEXT(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, type: int, pixels: AnyArray) -> None: ...

def glInitTexture3DEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
