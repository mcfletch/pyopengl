"""OpenGL.GLX.ARB.get_proc_address -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UByteArray

from OpenGL.raw.GLX._types import *

def glXGetProcAddressARB(procName: UByteArray) -> Any: ...

def glInitGetProcAddressARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
