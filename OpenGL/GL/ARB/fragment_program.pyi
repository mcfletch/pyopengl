"""OpenGL.GL.ARB.fragment_program -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, DoubleArray, DoubleArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_CURRENT_MATRIX_ARB: int
GL_CURRENT_MATRIX_STACK_DEPTH_ARB: int
GL_FRAGMENT_PROGRAM_ARB: int
GL_MATRIX0_ARB: int
GL_MATRIX10_ARB: int
GL_MATRIX11_ARB: int
GL_MATRIX12_ARB: int
GL_MATRIX13_ARB: int
GL_MATRIX14_ARB: int
GL_MATRIX15_ARB: int
GL_MATRIX16_ARB: int
GL_MATRIX17_ARB: int
GL_MATRIX18_ARB: int
GL_MATRIX19_ARB: int
GL_MATRIX1_ARB: int
GL_MATRIX20_ARB: int
GL_MATRIX21_ARB: int
GL_MATRIX22_ARB: int
GL_MATRIX23_ARB: int
GL_MATRIX24_ARB: int
GL_MATRIX25_ARB: int
GL_MATRIX26_ARB: int
GL_MATRIX27_ARB: int
GL_MATRIX28_ARB: int
GL_MATRIX29_ARB: int
GL_MATRIX2_ARB: int
GL_MATRIX30_ARB: int
GL_MATRIX31_ARB: int
GL_MATRIX3_ARB: int
GL_MATRIX4_ARB: int
GL_MATRIX5_ARB: int
GL_MATRIX6_ARB: int
GL_MATRIX7_ARB: int
GL_MATRIX8_ARB: int
GL_MATRIX9_ARB: int
GL_MAX_PROGRAM_ALU_INSTRUCTIONS_ARB: int
GL_MAX_PROGRAM_ATTRIBS_ARB: int
GL_MAX_PROGRAM_ENV_PARAMETERS_ARB: int
GL_MAX_PROGRAM_INSTRUCTIONS_ARB: int
GL_MAX_PROGRAM_LOCAL_PARAMETERS_ARB: int
GL_MAX_PROGRAM_MATRICES_ARB: int
GL_MAX_PROGRAM_MATRIX_STACK_DEPTH_ARB: int
GL_MAX_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB: int
GL_MAX_PROGRAM_NATIVE_ATTRIBS_ARB: int
GL_MAX_PROGRAM_NATIVE_INSTRUCTIONS_ARB: int
GL_MAX_PROGRAM_NATIVE_PARAMETERS_ARB: int
GL_MAX_PROGRAM_NATIVE_TEMPORARIES_ARB: int
GL_MAX_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB: int
GL_MAX_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB: int
GL_MAX_PROGRAM_PARAMETERS_ARB: int
GL_MAX_PROGRAM_TEMPORARIES_ARB: int
GL_MAX_PROGRAM_TEX_INDIRECTIONS_ARB: int
GL_MAX_PROGRAM_TEX_INSTRUCTIONS_ARB: int
GL_MAX_TEXTURE_COORDS_ARB: int
GL_MAX_TEXTURE_IMAGE_UNITS_ARB: int
GL_PROGRAM_ALU_INSTRUCTIONS_ARB: int
GL_PROGRAM_ATTRIBS_ARB: int
GL_PROGRAM_BINDING_ARB: int
GL_PROGRAM_ERROR_POSITION_ARB: int
GL_PROGRAM_ERROR_STRING_ARB: int
GL_PROGRAM_FORMAT_ARB: int
GL_PROGRAM_FORMAT_ASCII_ARB: int
GL_PROGRAM_INSTRUCTIONS_ARB: int
GL_PROGRAM_LENGTH_ARB: int
GL_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB: int
GL_PROGRAM_NATIVE_ATTRIBS_ARB: int
GL_PROGRAM_NATIVE_INSTRUCTIONS_ARB: int
GL_PROGRAM_NATIVE_PARAMETERS_ARB: int
GL_PROGRAM_NATIVE_TEMPORARIES_ARB: int
GL_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB: int
GL_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB: int
GL_PROGRAM_PARAMETERS_ARB: int
GL_PROGRAM_STRING_ARB: int
GL_PROGRAM_TEMPORARIES_ARB: int
GL_PROGRAM_TEX_INDIRECTIONS_ARB: int
GL_PROGRAM_TEX_INSTRUCTIONS_ARB: int
GL_PROGRAM_UNDER_NATIVE_LIMITS_ARB: int
GL_TRANSPOSE_CURRENT_MATRIX_ARB: int

def glBindProgramARB(target: int, program: int) -> None: ...
def glDeleteProgramsARB(n: int, programs: UIntArray) -> None: ...
def glGenProgramsARB(n: int, programs: UIntArray | None = None) -> UIntArrayResult: ...
def glGetProgramEnvParameterdvARB(target: int, index: int, params: DoubleArray | None = None) -> DoubleArrayResult: ...
def glGetProgramEnvParameterfvARB(target: int, index: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetProgramLocalParameterdvARB(target: int, index: int, params: DoubleArray | None = None) -> DoubleArrayResult: ...
def glGetProgramLocalParameterfvARB(target: int, index: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetProgramStringARB(target: int, pname: int, string: AnyArray) -> None: ...
def glGetProgramivARB(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glIsProgramARB(program: int) -> int: ...
def glProgramEnvParameter4dARB(target: int, index: int, x: float, y: float, z: float, w: float) -> None: ...
def glProgramEnvParameter4dvARB(target: int, index: int, params: DoubleArray) -> None: ...
def glProgramEnvParameter4fARB(target: int, index: int, x: float, y: float, z: float, w: float) -> None: ...
def glProgramEnvParameter4fvARB(target: int, index: int, params: FloatArray) -> None: ...
def glProgramLocalParameter4dARB(target: int, index: int, x: float, y: float, z: float, w: float) -> None: ...
def glProgramLocalParameter4dvARB(target: int, index: int, params: DoubleArray) -> None: ...
def glProgramLocalParameter4fARB(target: int, index: int, x: float, y: float, z: float, w: float) -> None: ...
def glProgramLocalParameter4fvARB(target: int, index: int, params: FloatArray) -> None: ...
def glProgramStringARB(target: int, format: int, len: int, string: AnyArray) -> None: ...

def glInitFragmentProgramARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
