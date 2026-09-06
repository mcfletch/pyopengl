"""OpenGL.GL.ARB.texture_compression -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_COMPRESSED_ALPHA_ARB: int
GL_COMPRESSED_INTENSITY_ARB: int
GL_COMPRESSED_LUMINANCE_ALPHA_ARB: int
GL_COMPRESSED_LUMINANCE_ARB: int
GL_COMPRESSED_RGBA_ARB: int
GL_COMPRESSED_RGB_ARB: int
GL_COMPRESSED_TEXTURE_FORMATS_ARB: int
GL_NUM_COMPRESSED_TEXTURE_FORMATS_ARB: int
GL_TEXTURE_COMPRESSED_ARB: int
GL_TEXTURE_COMPRESSED_IMAGE_SIZE_ARB: int
GL_TEXTURE_COMPRESSION_HINT_ARB: int

def glCompressedTexImage1DARB(target: int, level: int, internalformat: int, width: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexImage2DARB(target: int, level: int, internalformat: int, width: int, height: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexImage3DARB(target: int, level: int, internalformat: int, width: int, height: int, depth: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage1DARB(target: int, level: int, xoffset: int, width: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage2DARB(target: int, level: int, xoffset: int, yoffset: int, width: int, height: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage3DARB(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glGetCompressedTexImageARB(target: int, level: int, img: AnyArray) -> None: ...

def glInitTextureCompressionARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
