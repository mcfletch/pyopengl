"""OpenGL.GLES2.OVR.multiview_multisampled_render_to_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

def glFramebufferTextureMultisampleMultiviewOVR(target: int, attachment: int, texture: int, level: int, samples: int, baseViewIndex: int, numViews: int) -> None: ...

def glInitMultiviewMultisampledRenderToTextureOVR() -> bool: ...

def __getattr__(name: str) -> Any: ...
