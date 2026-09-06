"""OpenGL.GLES2.EXT.texture_view -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_TEXTURE_IMMUTABLE_LEVELS: int
GL_TEXTURE_VIEW_MIN_LAYER_EXT: int
GL_TEXTURE_VIEW_MIN_LEVEL_EXT: int
GL_TEXTURE_VIEW_NUM_LAYERS_EXT: int
GL_TEXTURE_VIEW_NUM_LEVELS_EXT: int

def glTextureViewEXT(texture: int, target: int, origtexture: int, internalformat: int, minlevel: int, numlevels: int, minlayer: int, numlayers: int) -> None: ...

def glInitTextureViewEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
