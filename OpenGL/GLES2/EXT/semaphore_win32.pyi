"""OpenGL.GLES2.EXT.semaphore_win32 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLES2._types import *

GL_D3D12_FENCE_VALUE_EXT: int
GL_DEVICE_LUID_EXT: int
GL_DEVICE_NODE_MASK_EXT: int
GL_HANDLE_TYPE_D3D12_FENCE_EXT: int
GL_HANDLE_TYPE_OPAQUE_WIN32_EXT: int
GL_HANDLE_TYPE_OPAQUE_WIN32_KMT_EXT: int
GL_LUID_SIZE_EXT: int

def glImportSemaphoreWin32HandleEXT(semaphore: int, handleType: int, handle: AnyArray) -> None: ...
def glImportSemaphoreWin32NameEXT(semaphore: int, handleType: int, name: AnyArray) -> None: ...

def glInitSemaphoreWin32EXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
