"""OpenGL.GL.EXT.framebuffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_COLOR_ATTACHMENT0_EXT: int
GL_COLOR_ATTACHMENT10_EXT: int
GL_COLOR_ATTACHMENT11_EXT: int
GL_COLOR_ATTACHMENT12_EXT: int
GL_COLOR_ATTACHMENT13_EXT: int
GL_COLOR_ATTACHMENT14_EXT: int
GL_COLOR_ATTACHMENT15_EXT: int
GL_COLOR_ATTACHMENT1_EXT: int
GL_COLOR_ATTACHMENT2_EXT: int
GL_COLOR_ATTACHMENT3_EXT: int
GL_COLOR_ATTACHMENT4_EXT: int
GL_COLOR_ATTACHMENT5_EXT: int
GL_COLOR_ATTACHMENT6_EXT: int
GL_COLOR_ATTACHMENT7_EXT: int
GL_COLOR_ATTACHMENT8_EXT: int
GL_COLOR_ATTACHMENT9_EXT: int
GL_DEPTH_ATTACHMENT_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_3D_ZOFFSET_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL_EXT: int
GL_FRAMEBUFFER_BINDING_EXT: int
GL_FRAMEBUFFER_COMPLETE_EXT: int
GL_FRAMEBUFFER_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER_EXT: int
GL_FRAMEBUFFER_UNSUPPORTED_EXT: int
GL_INVALID_FRAMEBUFFER_OPERATION_EXT: int
GL_MAX_COLOR_ATTACHMENTS_EXT: int
GL_MAX_RENDERBUFFER_SIZE_EXT: int
GL_RENDERBUFFER_ALPHA_SIZE_EXT: int
GL_RENDERBUFFER_BINDING_EXT: int
GL_RENDERBUFFER_BLUE_SIZE_EXT: int
GL_RENDERBUFFER_DEPTH_SIZE_EXT: int
GL_RENDERBUFFER_EXT: int
GL_RENDERBUFFER_GREEN_SIZE_EXT: int
GL_RENDERBUFFER_HEIGHT_EXT: int
GL_RENDERBUFFER_INTERNAL_FORMAT_EXT: int
GL_RENDERBUFFER_RED_SIZE_EXT: int
GL_RENDERBUFFER_STENCIL_SIZE_EXT: int
GL_RENDERBUFFER_WIDTH_EXT: int
GL_STENCIL_ATTACHMENT_EXT: int
GL_STENCIL_INDEX16_EXT: int
GL_STENCIL_INDEX1_EXT: int
GL_STENCIL_INDEX4_EXT: int
GL_STENCIL_INDEX8_EXT: int

def glBindFramebufferEXT(target: int, framebuffer: int) -> None: ...
def glBindRenderbufferEXT(target: int, renderbuffer: int) -> None: ...
def glCheckFramebufferStatusEXT(target: int) -> int: ...
def glDeleteFramebuffersEXT(n: int, framebuffers: UIntArray) -> None: ...
def glDeleteRenderbuffersEXT(n: int, renderbuffers: UIntArray) -> None: ...
def glFramebufferRenderbufferEXT(target: int, attachment: int, renderbuffertarget: int, renderbuffer: int) -> None: ...
def glFramebufferTexture1DEXT(target: int, attachment: int, textarget: int, texture: int, level: int) -> None: ...
def glFramebufferTexture2DEXT(target: int, attachment: int, textarget: int, texture: int, level: int) -> None: ...
def glFramebufferTexture3DEXT(target: int, attachment: int, textarget: int, texture: int, level: int, zoffset: int) -> None: ...
def glGenFramebuffersEXT(n: int, framebuffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGenRenderbuffersEXT(n: int, renderbuffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGenerateMipmapEXT(target: int) -> None: ...
def glGetFramebufferAttachmentParameterivEXT(target: int, attachment: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetRenderbufferParameterivEXT(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glIsFramebufferEXT(framebuffer: int) -> int: ...
def glIsRenderbufferEXT(renderbuffer: int) -> int: ...
def glRenderbufferStorageEXT(target: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferObjectEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
