"""OpenGL.GL.EXT.bindable_uniform -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_BINDABLE_UNIFORM_SIZE_EXT: int
GL_MAX_FRAGMENT_BINDABLE_UNIFORMS_EXT: int
GL_MAX_GEOMETRY_BINDABLE_UNIFORMS_EXT: int
GL_MAX_VERTEX_BINDABLE_UNIFORMS_EXT: int
GL_UNIFORM_BUFFER_BINDING_EXT: int
GL_UNIFORM_BUFFER_EXT: int

def glGetUniformBufferSizeEXT(program: int, location: int) -> int: ...
def glGetUniformOffsetEXT(program: int, location: int) -> int: ...
def glUniformBufferEXT(program: int, location: int, buffer: int) -> None: ...

def glInitBindableUniformEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
