"""OpenGL.GL.NVX.linked_gpu_multicast -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_LGPU_SEPARATE_STORAGE_BIT_NVX: int
GL_MAX_LGPU_GPUS_NVX: int

def glLGPUCopyImageSubDataNVX(sourceGpu: int, destinationGpuMask: int, srcName: int, srcTarget: int, srcLevel: int, srcX: int, srxY: int, srcZ: int, dstName: int, dstTarget: int, dstLevel: int, dstX: int, dstY: int, dstZ: int, width: int, height: int, depth: int) -> None: ...
def glLGPUInterlockNVX() -> None: ...
def glLGPUNamedBufferSubDataNVX(gpuMask: int, buffer: int, offset: int, size: int, data: AnyArray) -> None: ...

def glInitLinkedGpuMulticastNVX() -> bool: ...

def __getattr__(name: str) -> Any: ...
