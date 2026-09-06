"""OpenGL.GL.SGIS.texture4D -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_MAX_4D_TEXTURE_SIZE_SGIS: int
GL_PACK_IMAGE_DEPTH_SGIS: int
GL_PACK_SKIP_VOLUMES_SGIS: int
GL_PROXY_TEXTURE_4D_SGIS: int
GL_TEXTURE_4DSIZE_SGIS: int
GL_TEXTURE_4D_BINDING_SGIS: int
GL_TEXTURE_4D_SGIS: int
GL_TEXTURE_WRAP_Q_SGIS: int
GL_UNPACK_IMAGE_DEPTH_SGIS: int
GL_UNPACK_SKIP_VOLUMES_SGIS: int

def glTexImage4DSGIS(target: int, level: int, internalformat: int, width: int, height: int, depth: int, size4d: int, border: int, format: int, type: int, pixels: AnyArray) -> None: ...
def glTexSubImage4DSGIS(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, woffset: int, width: int, height: int, depth: int, size4d: int, format: int, type: int, pixels: AnyArray) -> None: ...

def glInitTexture4DSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
