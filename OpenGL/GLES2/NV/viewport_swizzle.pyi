"""OpenGL.GLES2.NV.viewport_swizzle -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_VIEWPORT_SWIZZLE_NEGATIVE_W_NV: int
GL_VIEWPORT_SWIZZLE_NEGATIVE_X_NV: int
GL_VIEWPORT_SWIZZLE_NEGATIVE_Y_NV: int
GL_VIEWPORT_SWIZZLE_NEGATIVE_Z_NV: int
GL_VIEWPORT_SWIZZLE_POSITIVE_W_NV: int
GL_VIEWPORT_SWIZZLE_POSITIVE_X_NV: int
GL_VIEWPORT_SWIZZLE_POSITIVE_Y_NV: int
GL_VIEWPORT_SWIZZLE_POSITIVE_Z_NV: int
GL_VIEWPORT_SWIZZLE_W_NV: int
GL_VIEWPORT_SWIZZLE_X_NV: int
GL_VIEWPORT_SWIZZLE_Y_NV: int
GL_VIEWPORT_SWIZZLE_Z_NV: int

def glViewportSwizzleNV(index: int, swizzlex: int, swizzley: int, swizzlez: int, swizzlew: int) -> None: ...

def glInitViewportSwizzleNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
