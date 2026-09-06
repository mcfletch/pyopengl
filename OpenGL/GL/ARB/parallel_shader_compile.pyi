"""OpenGL.GL.ARB.parallel_shader_compile -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_COMPLETION_STATUS_ARB: int
GL_MAX_SHADER_COMPILER_THREADS_ARB: int

def glMaxShaderCompilerThreadsARB(count: int) -> None: ...

def glInitParallelShaderCompileARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
