"""OpenGL.GL.NVX.gpu_memory_info -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX: int
GL_GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX: int
GL_GPU_MEMORY_INFO_EVICTED_MEMORY_NVX: int
GL_GPU_MEMORY_INFO_EVICTION_COUNT_NVX: int
GL_GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX: int

def glInitGpuMemoryInfoNVX() -> bool: ...

def __getattr__(name: str) -> Any: ...
