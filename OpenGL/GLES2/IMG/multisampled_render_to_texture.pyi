"""OpenGL.GLES2.IMG.multisampled_render_to_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_IMG: int
GL_MAX_SAMPLES_IMG: int
GL_RENDERBUFFER_SAMPLES_IMG: int
GL_TEXTURE_SAMPLES_IMG: int

def glFramebufferTexture2DMultisampleIMG(target: int, attachment: int, textarget: int, texture: int, level: int, samples: int) -> None: ...
def glRenderbufferStorageMultisampleIMG(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitMultisampledRenderToTextureIMG() -> bool: ...

def __getattr__(name: str) -> Any: ...
