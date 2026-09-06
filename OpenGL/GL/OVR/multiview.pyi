"""OpenGL.GL.OVR.multiview -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_BASE_VIEW_INDEX_OVR: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_NUM_VIEWS_OVR: int
GL_FRAMEBUFFER_INCOMPLETE_VIEW_TARGETS_OVR: int
GL_MAX_VIEWS_OVR: int

def glFramebufferTextureMultiviewOVR(target: int, attachment: int, texture: int, level: int, baseViewIndex: int, numViews: int) -> None: ...
def glNamedFramebufferTextureMultiviewOVR(framebuffer: int, attachment: int, texture: int, level: int, baseViewIndex: int, numViews: int) -> None: ...

def glInitMultiviewOVR() -> bool: ...

def __getattr__(name: str) -> Any: ...
