"""OpenGL.GL.EXT.memory_object_win32 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_DEVICE_LUID_EXT: int
GL_DEVICE_NODE_MASK_EXT: int
GL_HANDLE_TYPE_D3D11_IMAGE_EXT: int
GL_HANDLE_TYPE_D3D11_IMAGE_KMT_EXT: int
GL_HANDLE_TYPE_D3D12_RESOURCE_EXT: int
GL_HANDLE_TYPE_D3D12_TILEPOOL_EXT: int
GL_HANDLE_TYPE_OPAQUE_WIN32_EXT: int
GL_HANDLE_TYPE_OPAQUE_WIN32_KMT_EXT: int
GL_LUID_SIZE_EXT: int

def glImportMemoryWin32HandleEXT(memory: int, size: int, handleType: int, handle: AnyArray) -> None: ...
def glImportMemoryWin32NameEXT(memory: int, size: int, handleType: int, name: AnyArray) -> None: ...

def glInitMemoryObjectWin32EXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
