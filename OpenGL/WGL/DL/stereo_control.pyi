"""OpenGL.WGL.DL.stereo_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

WGL_STEREO_EMITTER_DISABLE_3DL: int
WGL_STEREO_EMITTER_ENABLE_3DL: int
WGL_STEREO_POLARITY_INVERT_3DL: int
WGL_STEREO_POLARITY_NORMAL_3DL: int

def wglSetStereoEmitterState3DL(hDC: Any, uState: int) -> int: ...

def glInitStereoControlDL() -> bool: ...

def __getattr__(name: str) -> Any: ...
