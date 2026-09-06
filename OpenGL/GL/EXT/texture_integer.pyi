"""OpenGL.GL.EXT.texture_integer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ALPHA16I_EXT: int
GL_ALPHA16UI_EXT: int
GL_ALPHA32I_EXT: int
GL_ALPHA32UI_EXT: int
GL_ALPHA8I_EXT: int
GL_ALPHA8UI_EXT: int
GL_ALPHA_INTEGER_EXT: int
GL_BGRA_INTEGER_EXT: int
GL_BGR_INTEGER_EXT: int
GL_BLUE_INTEGER_EXT: int
GL_GREEN_INTEGER_EXT: int
GL_INTENSITY16I_EXT: int
GL_INTENSITY16UI_EXT: int
GL_INTENSITY32I_EXT: int
GL_INTENSITY32UI_EXT: int
GL_INTENSITY8I_EXT: int
GL_INTENSITY8UI_EXT: int
GL_LUMINANCE16I_EXT: int
GL_LUMINANCE16UI_EXT: int
GL_LUMINANCE32I_EXT: int
GL_LUMINANCE32UI_EXT: int
GL_LUMINANCE8I_EXT: int
GL_LUMINANCE8UI_EXT: int
GL_LUMINANCE_ALPHA16I_EXT: int
GL_LUMINANCE_ALPHA16UI_EXT: int
GL_LUMINANCE_ALPHA32I_EXT: int
GL_LUMINANCE_ALPHA32UI_EXT: int
GL_LUMINANCE_ALPHA8I_EXT: int
GL_LUMINANCE_ALPHA8UI_EXT: int
GL_LUMINANCE_ALPHA_INTEGER_EXT: int
GL_LUMINANCE_INTEGER_EXT: int
GL_RED_INTEGER_EXT: int
GL_RGB16I_EXT: int
GL_RGB16UI_EXT: int
GL_RGB32I_EXT: int
GL_RGB32UI_EXT: int
GL_RGB8I_EXT: int
GL_RGB8UI_EXT: int
GL_RGBA16I_EXT: int
GL_RGBA16UI_EXT: int
GL_RGBA32I_EXT: int
GL_RGBA32UI_EXT: int
GL_RGBA8I_EXT: int
GL_RGBA8UI_EXT: int
GL_RGBA_INTEGER_EXT: int
GL_RGBA_INTEGER_MODE_EXT: int
GL_RGB_INTEGER_EXT: int

def glClearColorIiEXT(red: int, green: int, blue: int, alpha: int) -> None: ...
def glClearColorIuiEXT(red: int, green: int, blue: int, alpha: int) -> None: ...
def glGetTexParameterIivEXT(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetTexParameterIuivEXT(target: int, pname: int, params: UIntArray | None = None) -> UIntArrayResult: ...
def glTexParameterIivEXT(target: int, pname: int, params: IntArray) -> None: ...
def glTexParameterIuivEXT(target: int, pname: int, params: UIntArray) -> None: ...

def glInitTextureIntegerEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
