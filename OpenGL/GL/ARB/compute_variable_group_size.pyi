"""OpenGL.GL.ARB.compute_variable_group_size -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_COMPUTE_FIXED_GROUP_INVOCATIONS_ARB: int
GL_MAX_COMPUTE_FIXED_GROUP_SIZE_ARB: int
GL_MAX_COMPUTE_VARIABLE_GROUP_INVOCATIONS_ARB: int
GL_MAX_COMPUTE_VARIABLE_GROUP_SIZE_ARB: int

def glDispatchComputeGroupSizeARB(num_groups_x: int, num_groups_y: int, num_groups_z: int, group_size_x: int, group_size_y: int, group_size_z: int) -> None: ...

def glInitComputeVariableGroupSizeARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
