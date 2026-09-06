"""OpenGL.GLES2.EXT.multisampled_render_to_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_SAMPLES_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_EXT: int
GL_MAX_SAMPLES_EXT: int
GL_RENDERBUFFER_SAMPLES_EXT: int

def glFramebufferTexture2DMultisampleEXT(target: int, attachment: int, textarget: int, texture: int, level: int, samples: int) -> None: ...
def glRenderbufferStorageMultisampleEXT(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitMultisampledRenderToTextureEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
