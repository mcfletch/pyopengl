"""OpenGL.GLX.MESA.pixmap_colormap -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXCreateGLXPixmapMESA(dpy: AnyArray, visual: AnyArray, pixmap: Any, cmap: Any) -> Any: ...

def glInitPixmapColormapMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
