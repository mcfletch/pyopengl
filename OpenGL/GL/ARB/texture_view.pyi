"""OpenGL.GL.ARB.texture_view -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_TEXTURE_IMMUTABLE_LEVELS: int
GL_TEXTURE_VIEW_MIN_LAYER: int
GL_TEXTURE_VIEW_MIN_LEVEL: int
GL_TEXTURE_VIEW_NUM_LAYERS: int
GL_TEXTURE_VIEW_NUM_LEVELS: int

def glTextureView(texture: int, target: int, origtexture: int, internalformat: int, minlevel: int, numlevels: int, minlayer: int, numlayers: int) -> None: ...

def glInitTextureViewARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
