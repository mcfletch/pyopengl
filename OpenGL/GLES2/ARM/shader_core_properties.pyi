"""OpenGL.GLES2.ARM.shader_core_properties -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_SHADER_CORE_ACTIVE_COUNT_ARM: int
GL_SHADER_CORE_COUNT_ARM: int
GL_SHADER_CORE_FMA_RATE_ARM: int
GL_SHADER_CORE_MAX_WARP_COUNT_ARM: int
GL_SHADER_CORE_PIXEL_RATE_ARM: int
GL_SHADER_CORE_PRESENT_MASK_ARM: int
GL_SHADER_CORE_TEXEL_RATE_ARM: int

def glMaxActiveShaderCoresARM(count: int) -> None: ...

def glInitShaderCorePropertiesARM() -> bool: ...

def __getattr__(name: str) -> Any: ...
