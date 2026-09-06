"""OpenGL.GLES2.EXT.texture_storage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_ALPHA16F_EXT: int
GL_ALPHA32F_EXT: int
GL_ALPHA8_EXT: int
GL_BGRA8_EXT: int
GL_LUMINANCE16F_EXT: int
GL_LUMINANCE32F_EXT: int
GL_LUMINANCE8_ALPHA8_EXT: int
GL_LUMINANCE8_EXT: int
GL_LUMINANCE_ALPHA16F_EXT: int
GL_LUMINANCE_ALPHA32F_EXT: int
GL_R16F_EXT: int
GL_R32F_EXT: int
GL_R8_EXT: int
GL_RG16F_EXT: int
GL_RG32F_EXT: int
GL_RG8_EXT: int
GL_RGB10_A2_EXT: int
GL_RGB10_EXT: int
GL_RGB16F_EXT: int
GL_RGB32F_EXT: int
GL_RGBA16F_EXT: int
GL_RGBA32F_EXT: int
GL_TEXTURE_IMMUTABLE_FORMAT_EXT: int

def glTexStorage1DEXT(target: int, levels: int, internalformat: int, width: int) -> None: ...
def glTexStorage2DEXT(target: int, levels: int, internalformat: int, width: int, height: int) -> None: ...
def glTexStorage3DEXT(target: int, levels: int, internalformat: int, width: int, height: int, depth: int) -> None: ...
def glTextureStorage1DEXT(texture: int, target: int, levels: int, internalformat: int, width: int) -> None: ...
def glTextureStorage2DEXT(texture: int, target: int, levels: int, internalformat: int, width: int, height: int) -> None: ...
def glTextureStorage3DEXT(texture: int, target: int, levels: int, internalformat: int, width: int, height: int, depth: int) -> None: ...

def glInitTextureStorageEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
