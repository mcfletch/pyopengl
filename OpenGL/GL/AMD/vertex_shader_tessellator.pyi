"""OpenGL.GL.AMD.vertex_shader_tessellator -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_CONTINUOUS_AMD: int
GL_DISCRETE_AMD: int
GL_INT_SAMPLER_BUFFER_AMD: int
GL_SAMPLER_BUFFER_AMD: int
GL_TESSELLATION_FACTOR_AMD: int
GL_TESSELLATION_MODE_AMD: int
GL_UNSIGNED_INT_SAMPLER_BUFFER_AMD: int

def glTessellationFactorAMD(factor: float) -> None: ...
def glTessellationModeAMD(mode: int) -> None: ...

def glInitVertexShaderTessellatorAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
