"""OpenGL.GLES2.AMD.framebuffer_multisample_advanced -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_MAX_COLOR_FRAMEBUFFER_SAMPLES_AMD: int
GL_MAX_COLOR_FRAMEBUFFER_STORAGE_SAMPLES_AMD: int
GL_MAX_DEPTH_STENCIL_FRAMEBUFFER_SAMPLES_AMD: int
GL_NUM_SUPPORTED_MULTISAMPLE_MODES_AMD: int
GL_RENDERBUFFER_STORAGE_SAMPLES_AMD: int
GL_SUPPORTED_MULTISAMPLE_MODES_AMD: int

def glNamedRenderbufferStorageMultisampleAdvancedAMD(renderbuffer: int, samples: int, storageSamples: int, internalformat: int, width: int, height: int) -> None: ...
def glRenderbufferStorageMultisampleAdvancedAMD(target: int, samples: int, storageSamples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferMultisampleAdvancedAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
