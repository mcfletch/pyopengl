"""OpenGL.GL.EXT.light_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ATTENUATION_EXT: int
GL_FRAGMENT_COLOR_EXT: int
GL_FRAGMENT_DEPTH_EXT: int
GL_FRAGMENT_MATERIAL_EXT: int
GL_FRAGMENT_NORMAL_EXT: int
GL_SHADOW_ATTENUATION_EXT: int
GL_TEXTURE_APPLICATION_MODE_EXT: int
GL_TEXTURE_LIGHT_EXT: int
GL_TEXTURE_MATERIAL_FACE_EXT: int
GL_TEXTURE_MATERIAL_PARAMETER_EXT: int

def glApplyTextureEXT(mode: int) -> None: ...
def glTextureLightEXT(pname: int) -> None: ...
def glTextureMaterialEXT(face: int, mode: int) -> None: ...

def glInitLightTextureEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
