"""OpenGL.GLES2.KHR.parallel_shader_compile -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_COMPLETION_STATUS_KHR: int
GL_MAX_SHADER_COMPILER_THREADS_KHR: int

def glMaxShaderCompilerThreadsKHR(count: int) -> None: ...

def glInitParallelShaderCompileKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
