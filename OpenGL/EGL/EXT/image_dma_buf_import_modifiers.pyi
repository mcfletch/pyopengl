"""OpenGL.EGL.EXT.image_dma_buf_import_modifiers -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray, UInt64Array

from OpenGL.raw.EGL._types import *

EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT: int
EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT: int
EGL_DMA_BUF_PLANE1_MODIFIER_HI_EXT: int
EGL_DMA_BUF_PLANE1_MODIFIER_LO_EXT: int
EGL_DMA_BUF_PLANE2_MODIFIER_HI_EXT: int
EGL_DMA_BUF_PLANE2_MODIFIER_LO_EXT: int
EGL_DMA_BUF_PLANE3_FD_EXT: int
EGL_DMA_BUF_PLANE3_MODIFIER_HI_EXT: int
EGL_DMA_BUF_PLANE3_MODIFIER_LO_EXT: int
EGL_DMA_BUF_PLANE3_OFFSET_EXT: int
EGL_DMA_BUF_PLANE3_PITCH_EXT: int

def eglQueryDmaBufFormatsEXT(dpy: Any, max_formats: int, formats: IntArray, num_formats: IntArray) -> int: ...
def eglQueryDmaBufModifiersEXT(dpy: Any, format: int, max_modifiers: int, modifiers: UInt64Array, external_only: AnyArray, num_modifiers: IntArray) -> int: ...

def eglInitImageDmaBufImportModifiersEXT(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
