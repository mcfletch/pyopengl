"""OpenGL.GL.EXT.x11_sync_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_SYNC_X11_FENCE_EXT: int

def glImportSyncEXT(external_sync_type: int, external_sync: int, flags: int) -> Any: ...

def glInitX11SyncObjectEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
