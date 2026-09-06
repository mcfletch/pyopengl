"""OpenGL.GL.ARB.program_interface_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray

from OpenGL.raw.GL._types import *

GL_ACTIVE_RESOURCES: int
GL_ACTIVE_VARIABLES: int
GL_ARRAY_SIZE: int
GL_ARRAY_STRIDE: int
GL_ATOMIC_COUNTER_BUFFER: int
GL_ATOMIC_COUNTER_BUFFER_INDEX: int
GL_BLOCK_INDEX: int
GL_BUFFER_BINDING: int
GL_BUFFER_DATA_SIZE: int
GL_BUFFER_VARIABLE: int
GL_COMPATIBLE_SUBROUTINES: int
GL_COMPUTE_SUBROUTINE: int
GL_COMPUTE_SUBROUTINE_UNIFORM: int
GL_FRAGMENT_SUBROUTINE: int
GL_FRAGMENT_SUBROUTINE_UNIFORM: int
GL_GEOMETRY_SUBROUTINE: int
GL_GEOMETRY_SUBROUTINE_UNIFORM: int
GL_IS_PER_PATCH: int
GL_IS_ROW_MAJOR: int
GL_LOCATION: int
GL_LOCATION_INDEX: int
GL_MATRIX_STRIDE: int
GL_MAX_NAME_LENGTH: int
GL_MAX_NUM_ACTIVE_VARIABLES: int
GL_MAX_NUM_COMPATIBLE_SUBROUTINES: int
GL_NAME_LENGTH: int
GL_NUM_ACTIVE_VARIABLES: int
GL_NUM_COMPATIBLE_SUBROUTINES: int
GL_OFFSET: int
GL_PROGRAM_INPUT: int
GL_PROGRAM_OUTPUT: int
GL_REFERENCED_BY_COMPUTE_SHADER: int
GL_REFERENCED_BY_FRAGMENT_SHADER: int
GL_REFERENCED_BY_GEOMETRY_SHADER: int
GL_REFERENCED_BY_TESS_CONTROL_SHADER: int
GL_REFERENCED_BY_TESS_EVALUATION_SHADER: int
GL_REFERENCED_BY_VERTEX_SHADER: int
GL_SHADER_STORAGE_BLOCK: int
GL_TESS_CONTROL_SUBROUTINE: int
GL_TESS_CONTROL_SUBROUTINE_UNIFORM: int
GL_TESS_EVALUATION_SUBROUTINE: int
GL_TESS_EVALUATION_SUBROUTINE_UNIFORM: int
GL_TOP_LEVEL_ARRAY_SIZE: int
GL_TOP_LEVEL_ARRAY_STRIDE: int
GL_TRANSFORM_FEEDBACK_VARYING: int
GL_TYPE: int
GL_UNIFORM: int
GL_UNIFORM_BLOCK: int
GL_VERTEX_SUBROUTINE: int
GL_VERTEX_SUBROUTINE_UNIFORM: int

def glGetProgramInterfaceiv(program: int, programInterface: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetProgramResourceIndex(program: int, programInterface: int, name: ByteArray) -> int: ...
def glGetProgramResourceLocation(program: int, programInterface: int, name: ByteArray) -> int: ...
def glGetProgramResourceLocationIndex(program: int, programInterface: int, name: ByteArray) -> int: ...
def glGetProgramResourceName(program: int, programInterface: int, index: int, bufSize: int, length: IntArray | None = None, name: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult]: ...
def glGetProgramResourceiv(program: int, programInterface: int, index: int, propCount: int, props: UIntArray, count: int, length: IntArray | None = None, params: IntArray | None = None) -> tuple[IntArrayResult, IntArrayResult]: ...

def glInitProgramInterfaceQueryARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
