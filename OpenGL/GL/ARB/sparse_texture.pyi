"""OpenGL.GL.ARB.sparse_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_SPARSE_3D_TEXTURE_SIZE_ARB: int
GL_MAX_SPARSE_ARRAY_TEXTURE_LAYERS_ARB: int
GL_MAX_SPARSE_TEXTURE_SIZE_ARB: int
GL_NUM_SPARSE_LEVELS_ARB: int
GL_NUM_VIRTUAL_PAGE_SIZES_ARB: int
GL_SPARSE_TEXTURE_FULL_ARRAY_CUBE_MIPMAPS_ARB: int
GL_TEXTURE_SPARSE_ARB: int
GL_VIRTUAL_PAGE_SIZE_INDEX_ARB: int
GL_VIRTUAL_PAGE_SIZE_X_ARB: int
GL_VIRTUAL_PAGE_SIZE_Y_ARB: int
GL_VIRTUAL_PAGE_SIZE_Z_ARB: int

def glTexPageCommitmentARB(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, commit: int) -> None: ...

def glInitSparseTextureARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
