"""OpenGL.EGL.NV.cuda_event -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_CUDA_EVENT_HANDLE_NV: int
EGL_SYNC_CUDA_EVENT_COMPLETE_NV: int
EGL_SYNC_CUDA_EVENT_NV: int

def glInitCudaEventNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
