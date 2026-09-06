"""OpenGL.GLES1.OES.framebuffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UIntArray

from OpenGL.raw.GLES1._types import *

GL_COLOR_ATTACHMENT0_OES: int
GL_DEPTH_ATTACHMENT_OES: int
GL_DEPTH_COMPONENT16_OES: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME_OES: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE_OES: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE_OES: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL_OES: int
GL_FRAMEBUFFER_BINDING_OES: int
GL_FRAMEBUFFER_COMPLETE_OES: int
GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_OES: int
GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_OES: int
GL_FRAMEBUFFER_INCOMPLETE_FORMATS_OES: int
GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_OES: int
GL_FRAMEBUFFER_OES: int
GL_FRAMEBUFFER_UNSUPPORTED_OES: int
GL_INVALID_FRAMEBUFFER_OPERATION_OES: int
GL_MAX_RENDERBUFFER_SIZE_OES: int
GL_NONE_OES: int
GL_RENDERBUFFER_ALPHA_SIZE_OES: int
GL_RENDERBUFFER_BINDING_OES: int
GL_RENDERBUFFER_BLUE_SIZE_OES: int
GL_RENDERBUFFER_DEPTH_SIZE_OES: int
GL_RENDERBUFFER_GREEN_SIZE_OES: int
GL_RENDERBUFFER_HEIGHT_OES: int
GL_RENDERBUFFER_INTERNAL_FORMAT_OES: int
GL_RENDERBUFFER_OES: int
GL_RENDERBUFFER_RED_SIZE_OES: int
GL_RENDERBUFFER_STENCIL_SIZE_OES: int
GL_RENDERBUFFER_WIDTH_OES: int
GL_RGB565_OES: int
GL_RGB5_A1_OES: int
GL_RGBA4_OES: int
GL_STENCIL_ATTACHMENT_OES: int

def glBindFramebufferOES(target: int, framebuffer: int) -> None: ...
def glBindRenderbufferOES(target: int, renderbuffer: int) -> None: ...
def glCheckFramebufferStatusOES(target: int) -> int: ...
def glDeleteFramebuffersOES(n: int, framebuffers: UIntArray) -> None: ...
def glDeleteRenderbuffersOES(n: int, renderbuffers: UIntArray) -> None: ...
def glFramebufferRenderbufferOES(target: int, attachment: int, renderbuffertarget: int, renderbuffer: int) -> None: ...
def glFramebufferTexture2DOES(target: int, attachment: int, textarget: int, texture: int, level: int) -> None: ...
def glGenFramebuffersOES(n: int, framebuffers: UIntArray) -> None: ...
def glGenRenderbuffersOES(n: int, renderbuffers: UIntArray) -> None: ...
def glGenerateMipmapOES(target: int) -> None: ...
def glGetFramebufferAttachmentParameterivOES(target: int, attachment: int, pname: int, params: IntArray) -> None: ...
def glGetRenderbufferParameterivOES(target: int, pname: int, params: IntArray) -> None: ...
def glIsFramebufferOES(framebuffer: int) -> int: ...
def glIsRenderbufferOES(renderbuffer: int) -> int: ...
def glRenderbufferStorageOES(target: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferObjectOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
