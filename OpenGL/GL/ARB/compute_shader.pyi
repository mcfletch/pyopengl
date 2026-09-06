"""OpenGL.GL.ARB.compute_shader -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ATOMIC_COUNTER_BUFFER_REFERENCED_BY_COMPUTE_SHADER: int
GL_COMPUTE_SHADER: int
GL_COMPUTE_SHADER_BIT: int
GL_COMPUTE_WORK_GROUP_SIZE: int
GL_DISPATCH_INDIRECT_BUFFER: int
GL_DISPATCH_INDIRECT_BUFFER_BINDING: int
GL_MAX_COMBINED_COMPUTE_UNIFORM_COMPONENTS: int
GL_MAX_COMPUTE_ATOMIC_COUNTERS: int
GL_MAX_COMPUTE_ATOMIC_COUNTER_BUFFERS: int
GL_MAX_COMPUTE_IMAGE_UNIFORMS: int
GL_MAX_COMPUTE_SHARED_MEMORY_SIZE: int
GL_MAX_COMPUTE_TEXTURE_IMAGE_UNITS: int
GL_MAX_COMPUTE_UNIFORM_BLOCKS: int
GL_MAX_COMPUTE_UNIFORM_COMPONENTS: int
GL_MAX_COMPUTE_WORK_GROUP_COUNT: int
GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS: int
GL_MAX_COMPUTE_WORK_GROUP_SIZE: int
GL_UNIFORM_BLOCK_REFERENCED_BY_COMPUTE_SHADER: int

def glDispatchCompute(num_groups_x: int, num_groups_y: int, num_groups_z: int) -> None: ...
def glDispatchComputeIndirect(indirect: int) -> None: ...

def glInitComputeShaderARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
