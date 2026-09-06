"""OpenGL.GL.NV.vdpau_interop2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, UIntArray

from OpenGL.raw.GL._types import *

def glVDPAURegisterVideoSurfaceWithPictureStructureNV(vdpSurface: AnyArray, target: int, numTextureNames: int, textureNames: UIntArray, isFrameStructure: bool) -> int: ...

def glInitVdpauInterop2NV() -> bool: ...

def __getattr__(name: str) -> Any: ...
