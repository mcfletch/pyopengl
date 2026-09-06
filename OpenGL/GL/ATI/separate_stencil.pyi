"""OpenGL.GL.ATI.separate_stencil -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_STENCIL_BACK_FAIL_ATI: int
GL_STENCIL_BACK_FUNC_ATI: int
GL_STENCIL_BACK_PASS_DEPTH_FAIL_ATI: int
GL_STENCIL_BACK_PASS_DEPTH_PASS_ATI: int

def glStencilFuncSeparateATI(frontfunc: int, backfunc: int, ref: int, mask: int) -> None: ...
def glStencilOpSeparateATI(face: int, sfail: int, dpfail: int, dppass: int) -> None: ...

def glInitSeparateStencilATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
