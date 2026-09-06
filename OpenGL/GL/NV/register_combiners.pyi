"""OpenGL.GL.NV.register_combiners -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_BIAS_BY_NEGATIVE_ONE_HALF_NV: int
GL_COLOR_SUM_CLAMP_NV: int
GL_COMBINER0_NV: int
GL_COMBINER1_NV: int
GL_COMBINER2_NV: int
GL_COMBINER3_NV: int
GL_COMBINER4_NV: int
GL_COMBINER5_NV: int
GL_COMBINER6_NV: int
GL_COMBINER7_NV: int
GL_COMBINER_AB_DOT_PRODUCT_NV: int
GL_COMBINER_AB_OUTPUT_NV: int
GL_COMBINER_BIAS_NV: int
GL_COMBINER_CD_DOT_PRODUCT_NV: int
GL_COMBINER_CD_OUTPUT_NV: int
GL_COMBINER_COMPONENT_USAGE_NV: int
GL_COMBINER_INPUT_NV: int
GL_COMBINER_MAPPING_NV: int
GL_COMBINER_MUX_SUM_NV: int
GL_COMBINER_SCALE_NV: int
GL_COMBINER_SUM_OUTPUT_NV: int
GL_CONSTANT_COLOR0_NV: int
GL_CONSTANT_COLOR1_NV: int
GL_DISCARD_NV: int
GL_EXPAND_NEGATE_NV: int
GL_EXPAND_NORMAL_NV: int
GL_E_TIMES_F_NV: int
GL_FOG: int
GL_HALF_BIAS_NEGATE_NV: int
GL_HALF_BIAS_NORMAL_NV: int
GL_MAX_GENERAL_COMBINERS_NV: int
GL_NONE: int
GL_NUM_GENERAL_COMBINERS_NV: int
GL_PRIMARY_COLOR_NV: int
GL_REGISTER_COMBINERS_NV: int
GL_SCALE_BY_FOUR_NV: int
GL_SCALE_BY_ONE_HALF_NV: int
GL_SCALE_BY_TWO_NV: int
GL_SECONDARY_COLOR_NV: int
GL_SIGNED_IDENTITY_NV: int
GL_SIGNED_NEGATE_NV: int
GL_SPARE0_NV: int
GL_SPARE0_PLUS_SECONDARY_COLOR_NV: int
GL_SPARE1_NV: int
GL_TEXTURE0_ARB: int
GL_TEXTURE1_ARB: int
GL_UNSIGNED_IDENTITY_NV: int
GL_UNSIGNED_INVERT_NV: int
GL_VARIABLE_A_NV: int
GL_VARIABLE_B_NV: int
GL_VARIABLE_C_NV: int
GL_VARIABLE_D_NV: int
GL_VARIABLE_E_NV: int
GL_VARIABLE_F_NV: int
GL_VARIABLE_G_NV: int
GL_ZERO: int

def glCombinerInputNV(stage: int, portion: int, variable: int, input: int, mapping: int, componentUsage: int) -> None: ...
def glCombinerOutputNV(stage: int, portion: int, abOutput: int, cdOutput: int, sumOutput: int, scale: int, bias: int, abDotProduct: bool, cdDotProduct: bool, muxSum: bool) -> None: ...
def glCombinerParameterfNV(pname: int, param: float) -> None: ...
def glCombinerParameterfvNV(pname: int, params: FloatArray) -> None: ...
def glCombinerParameteriNV(pname: int, param: int) -> None: ...
def glCombinerParameterivNV(pname: int, params: IntArray) -> None: ...
def glFinalCombinerInputNV(variable: int, input: int, mapping: int, componentUsage: int) -> None: ...
def glGetCombinerInputParameterfvNV(stage: int, portion: int, variable: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetCombinerInputParameterivNV(stage: int, portion: int, variable: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetCombinerOutputParameterfvNV(stage: int, portion: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetCombinerOutputParameterivNV(stage: int, portion: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetFinalCombinerInputParameterfvNV(variable: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetFinalCombinerInputParameterivNV(variable: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...

def glInitRegisterCombinersNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
