"""OpenGL.EGL.ANGLE.sync_control_rate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

def eglGetMscRateANGLE(dpy: Any, surface: Any, numerator: IntArray, denominator: IntArray) -> int: ...

def eglInitSyncControlRateANGLE(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
