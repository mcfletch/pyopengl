"""OpenGL.GL.EXT.texture_perturb_normal -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_PERTURB_EXT: int
GL_TEXTURE_NORMAL_EXT: int

def glTextureNormalEXT(mode: int) -> None: ...

def glInitTexturePerturbNormalEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
