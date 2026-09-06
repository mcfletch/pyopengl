"""OpenGL.GL.ARB.framebuffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_COLOR_ATTACHMENT0: int
GL_COLOR_ATTACHMENT1: int
GL_COLOR_ATTACHMENT10: int
GL_COLOR_ATTACHMENT11: int
GL_COLOR_ATTACHMENT12: int
GL_COLOR_ATTACHMENT13: int
GL_COLOR_ATTACHMENT14: int
GL_COLOR_ATTACHMENT15: int
GL_COLOR_ATTACHMENT2: int
GL_COLOR_ATTACHMENT3: int
GL_COLOR_ATTACHMENT4: int
GL_COLOR_ATTACHMENT5: int
GL_COLOR_ATTACHMENT6: int
GL_COLOR_ATTACHMENT7: int
GL_COLOR_ATTACHMENT8: int
GL_COLOR_ATTACHMENT9: int
GL_DEPTH24_STENCIL8: int
GL_DEPTH_ATTACHMENT: int
GL_DEPTH_STENCIL: int
GL_DEPTH_STENCIL_ATTACHMENT: int
GL_DRAW_FRAMEBUFFER: int
GL_DRAW_FRAMEBUFFER_BINDING: int
GL_FRAMEBUFFER: int
GL_FRAMEBUFFER_ATTACHMENT_ALPHA_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_BLUE_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_COLOR_ENCODING: int
GL_FRAMEBUFFER_ATTACHMENT_COMPONENT_TYPE: int
GL_FRAMEBUFFER_ATTACHMENT_DEPTH_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_GREEN_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME: int
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE: int
GL_FRAMEBUFFER_ATTACHMENT_RED_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_STENCIL_SIZE: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LAYER: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL: int
GL_FRAMEBUFFER_BINDING: int
GL_FRAMEBUFFER_COMPLETE: int
GL_FRAMEBUFFER_DEFAULT: int
GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT: int
GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER: int
GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: int
GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE: int
GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER: int
GL_FRAMEBUFFER_UNDEFINED: int
GL_FRAMEBUFFER_UNSUPPORTED: int
GL_INDEX: int
GL_INVALID_FRAMEBUFFER_OPERATION: int
GL_MAX_COLOR_ATTACHMENTS: int
GL_MAX_RENDERBUFFER_SIZE: int
GL_MAX_SAMPLES: int
GL_READ_FRAMEBUFFER: int
GL_READ_FRAMEBUFFER_BINDING: int
GL_RENDERBUFFER: int
GL_RENDERBUFFER_ALPHA_SIZE: int
GL_RENDERBUFFER_BINDING: int
GL_RENDERBUFFER_BLUE_SIZE: int
GL_RENDERBUFFER_DEPTH_SIZE: int
GL_RENDERBUFFER_GREEN_SIZE: int
GL_RENDERBUFFER_HEIGHT: int
GL_RENDERBUFFER_INTERNAL_FORMAT: int
GL_RENDERBUFFER_RED_SIZE: int
GL_RENDERBUFFER_SAMPLES: int
GL_RENDERBUFFER_STENCIL_SIZE: int
GL_RENDERBUFFER_WIDTH: int
GL_STENCIL_ATTACHMENT: int
GL_STENCIL_INDEX1: int
GL_STENCIL_INDEX16: int
GL_STENCIL_INDEX4: int
GL_STENCIL_INDEX8: int
GL_TEXTURE_STENCIL_SIZE: int
GL_UNSIGNED_INT_24_8: int
GL_UNSIGNED_NORMALIZED: int

def glBindFramebuffer(target: int, framebuffer: int) -> None: ...
def glBindRenderbuffer(target: int, renderbuffer: int) -> None: ...
def glBlitFramebuffer(srcX0: int, srcY0: int, srcX1: int, srcY1: int, dstX0: int, dstY0: int, dstX1: int, dstY1: int, mask: int, filter: int) -> None: ...
def glCheckFramebufferStatus(target: int) -> int: ...
def glDeleteFramebuffers(n: int, framebuffers: UIntArray) -> None: ...
def glDeleteRenderbuffers(n: int, renderbuffers: UIntArray) -> None: ...
def glFramebufferRenderbuffer(target: int, attachment: int, renderbuffertarget: int, renderbuffer: int) -> None: ...
def glFramebufferTexture1D(target: int, attachment: int, textarget: int, texture: int, level: int) -> None: ...
def glFramebufferTexture2D(target: int, attachment: int, textarget: int, texture: int, level: int) -> None: ...
def glFramebufferTexture3D(target: int, attachment: int, textarget: int, texture: int, level: int, zoffset: int) -> None: ...
def glFramebufferTextureLayer(target: int, attachment: int, texture: int, level: int, layer: int) -> None: ...
def glGenFramebuffers(n: int, framebuffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGenRenderbuffers(n: int, renderbuffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGenerateMipmap(target: int) -> None: ...
def glGetFramebufferAttachmentParameteriv(target: int, attachment: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetRenderbufferParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glIsFramebuffer(framebuffer: int) -> int: ...
def glIsRenderbuffer(renderbuffer: int) -> int: ...
def glRenderbufferStorage(target: int, internalformat: int, width: int, height: int) -> None: ...
def glRenderbufferStorageMultisample(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferObjectARB() -> bool: ...
GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS: int
GL_FRAMEBUFFER_INCOMPLETE_FORMATS: int

def __getattr__(name: str) -> Any: ...
