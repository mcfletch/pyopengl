"""OpenGL.GL.EXT.texture_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_COMPARE_REF_DEPTH_TO_TEXTURE_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LAYER_EXT: int
GL_MAX_ARRAY_TEXTURE_LAYERS_EXT: int
GL_PROXY_TEXTURE_1D_ARRAY_EXT: int
GL_PROXY_TEXTURE_2D_ARRAY_EXT: int
GL_TEXTURE_1D_ARRAY_EXT: int
GL_TEXTURE_2D_ARRAY_EXT: int
GL_TEXTURE_BINDING_1D_ARRAY_EXT: int
GL_TEXTURE_BINDING_2D_ARRAY_EXT: int

def glFramebufferTextureLayerEXT(target: int, attachment: int, texture: int, level: int, layer: int) -> None: ...

def glInitTextureArrayEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
