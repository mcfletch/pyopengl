"""OpenGL.GLES2.EXT.sparse_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_MAX_SPARSE_3D_TEXTURE_SIZE_EXT: int
GL_MAX_SPARSE_ARRAY_TEXTURE_LAYERS_EXT: int
GL_MAX_SPARSE_TEXTURE_SIZE_EXT: int
GL_NUM_SPARSE_LEVELS_EXT: int
GL_NUM_VIRTUAL_PAGE_SIZES_EXT: int
GL_SPARSE_TEXTURE_FULL_ARRAY_CUBE_MIPMAPS_EXT: int
GL_TEXTURE_2D: int
GL_TEXTURE_2D_ARRAY: int
GL_TEXTURE_3D: int
GL_TEXTURE_CUBE_MAP: int
GL_TEXTURE_CUBE_MAP_ARRAY_OES: int
GL_TEXTURE_SPARSE_EXT: int
GL_VIRTUAL_PAGE_SIZE_INDEX_EXT: int
GL_VIRTUAL_PAGE_SIZE_X_EXT: int
GL_VIRTUAL_PAGE_SIZE_Y_EXT: int
GL_VIRTUAL_PAGE_SIZE_Z_EXT: int

def glTexPageCommitmentEXT(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, commit: bool) -> None: ...

def glInitSparseTextureEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
