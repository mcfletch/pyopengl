"""OpenGL.GL.AMD.sparse_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_SPARSE_3D_TEXTURE_SIZE_AMD: int
GL_MAX_SPARSE_ARRAY_TEXTURE_LAYERS: int
GL_MAX_SPARSE_TEXTURE_SIZE_AMD: int
GL_MIN_LOD_WARNING_AMD: int
GL_MIN_SPARSE_LEVEL_AMD: int
GL_TEXTURE_STORAGE_SPARSE_BIT_AMD: int
GL_VIRTUAL_PAGE_SIZE_X_AMD: int
GL_VIRTUAL_PAGE_SIZE_Y_AMD: int
GL_VIRTUAL_PAGE_SIZE_Z_AMD: int

def glTexStorageSparseAMD(target: int, internalFormat: int, width: int, height: int, depth: int, layers: int, flags: int) -> None: ...
def glTextureStorageSparseAMD(texture: int, target: int, internalFormat: int, width: int, height: int, depth: int, layers: int, flags: int) -> None: ...

def glInitSparseTextureAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
