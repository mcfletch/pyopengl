"""OpenGL.GLES2.OES.texture_view -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_TEXTURE_IMMUTABLE_LEVELS: int
GL_TEXTURE_VIEW_MIN_LAYER_OES: int
GL_TEXTURE_VIEW_MIN_LEVEL_OES: int
GL_TEXTURE_VIEW_NUM_LAYERS_OES: int
GL_TEXTURE_VIEW_NUM_LEVELS_OES: int

def glTextureViewOES(texture: int, target: int, origtexture: int, internalformat: int, minlevel: int, numlevels: int, minlayer: int, numlayers: int) -> None: ...

def glInitTextureViewOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
