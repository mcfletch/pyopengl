"""OpenGL.GLES2.IMG.framebuffer_downsample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_DOWNSAMPLE_SCALES_IMG: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_SCALE_IMG: int
GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_AND_DOWNSAMPLE_IMG: int
GL_NUM_DOWNSAMPLE_SCALES_IMG: int

def glFramebufferTexture2DDownsampleIMG(target: int, attachment: int, textarget: int, texture: int, level: int, xscale: int, yscale: int) -> None: ...
def glFramebufferTextureLayerDownsampleIMG(target: int, attachment: int, texture: int, level: int, layer: int, xscale: int, yscale: int) -> None: ...

def glInitFramebufferDownsampleIMG() -> bool: ...

def __getattr__(name: str) -> Any: ...
