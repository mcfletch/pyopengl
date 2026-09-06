"""OpenGL.GL.ATI.fragment_shader -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_2X_BIT_ATI: int
GL_4X_BIT_ATI: int
GL_8X_BIT_ATI: int
GL_ADD_ATI: int
GL_BIAS_BIT_ATI: int
GL_BLUE_BIT_ATI: int
GL_CND0_ATI: int
GL_CND_ATI: int
GL_COLOR_ALPHA_PAIRING_ATI: int
GL_COMP_BIT_ATI: int
GL_CON_0_ATI: int
GL_CON_10_ATI: int
GL_CON_11_ATI: int
GL_CON_12_ATI: int
GL_CON_13_ATI: int
GL_CON_14_ATI: int
GL_CON_15_ATI: int
GL_CON_16_ATI: int
GL_CON_17_ATI: int
GL_CON_18_ATI: int
GL_CON_19_ATI: int
GL_CON_1_ATI: int
GL_CON_20_ATI: int
GL_CON_21_ATI: int
GL_CON_22_ATI: int
GL_CON_23_ATI: int
GL_CON_24_ATI: int
GL_CON_25_ATI: int
GL_CON_26_ATI: int
GL_CON_27_ATI: int
GL_CON_28_ATI: int
GL_CON_29_ATI: int
GL_CON_2_ATI: int
GL_CON_30_ATI: int
GL_CON_31_ATI: int
GL_CON_3_ATI: int
GL_CON_4_ATI: int
GL_CON_5_ATI: int
GL_CON_6_ATI: int
GL_CON_7_ATI: int
GL_CON_8_ATI: int
GL_CON_9_ATI: int
GL_DOT2_ADD_ATI: int
GL_DOT3_ATI: int
GL_DOT4_ATI: int
GL_EIGHTH_BIT_ATI: int
GL_FRAGMENT_SHADER_ATI: int
GL_GREEN_BIT_ATI: int
GL_HALF_BIT_ATI: int
GL_LERP_ATI: int
GL_MAD_ATI: int
GL_MOV_ATI: int
GL_MUL_ATI: int
GL_NEGATE_BIT_ATI: int
GL_NUM_FRAGMENT_CONSTANTS_ATI: int
GL_NUM_FRAGMENT_REGISTERS_ATI: int
GL_NUM_INPUT_INTERPOLATOR_COMPONENTS_ATI: int
GL_NUM_INSTRUCTIONS_PER_PASS_ATI: int
GL_NUM_INSTRUCTIONS_TOTAL_ATI: int
GL_NUM_LOOPBACK_COMPONENTS_ATI: int
GL_NUM_PASSES_ATI: int
GL_QUARTER_BIT_ATI: int
GL_RED_BIT_ATI: int
GL_REG_0_ATI: int
GL_REG_10_ATI: int
GL_REG_11_ATI: int
GL_REG_12_ATI: int
GL_REG_13_ATI: int
GL_REG_14_ATI: int
GL_REG_15_ATI: int
GL_REG_16_ATI: int
GL_REG_17_ATI: int
GL_REG_18_ATI: int
GL_REG_19_ATI: int
GL_REG_1_ATI: int
GL_REG_20_ATI: int
GL_REG_21_ATI: int
GL_REG_22_ATI: int
GL_REG_23_ATI: int
GL_REG_24_ATI: int
GL_REG_25_ATI: int
GL_REG_26_ATI: int
GL_REG_27_ATI: int
GL_REG_28_ATI: int
GL_REG_29_ATI: int
GL_REG_2_ATI: int
GL_REG_30_ATI: int
GL_REG_31_ATI: int
GL_REG_3_ATI: int
GL_REG_4_ATI: int
GL_REG_5_ATI: int
GL_REG_6_ATI: int
GL_REG_7_ATI: int
GL_REG_8_ATI: int
GL_REG_9_ATI: int
GL_SATURATE_BIT_ATI: int
GL_SECONDARY_INTERPOLATOR_ATI: int
GL_SUB_ATI: int
GL_SWIZZLE_STQ_ATI: int
GL_SWIZZLE_STQ_DQ_ATI: int
GL_SWIZZLE_STRQ_ATI: int
GL_SWIZZLE_STRQ_DQ_ATI: int
GL_SWIZZLE_STR_ATI: int
GL_SWIZZLE_STR_DR_ATI: int

def glAlphaFragmentOp1ATI(op: int, dst: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int) -> None: ...
def glAlphaFragmentOp2ATI(op: int, dst: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int, arg2: int, arg2Rep: int, arg2Mod: int) -> None: ...
def glAlphaFragmentOp3ATI(op: int, dst: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int, arg2: int, arg2Rep: int, arg2Mod: int, arg3: int, arg3Rep: int, arg3Mod: int) -> None: ...
def glBeginFragmentShaderATI() -> None: ...
def glBindFragmentShaderATI(id: int) -> None: ...
def glColorFragmentOp1ATI(op: int, dst: int, dstMask: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int) -> None: ...
def glColorFragmentOp2ATI(op: int, dst: int, dstMask: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int, arg2: int, arg2Rep: int, arg2Mod: int) -> None: ...
def glColorFragmentOp3ATI(op: int, dst: int, dstMask: int, dstMod: int, arg1: int, arg1Rep: int, arg1Mod: int, arg2: int, arg2Rep: int, arg2Mod: int, arg3: int, arg3Rep: int, arg3Mod: int) -> None: ...
def glDeleteFragmentShaderATI(id: int) -> None: ...
def glEndFragmentShaderATI() -> None: ...
def glGenFragmentShadersATI(range: int) -> int: ...
def glPassTexCoordATI(dst: int, coord: int, swizzle: int) -> None: ...
def glSampleMapATI(dst: int, interp: int, swizzle: int) -> None: ...
def glSetFragmentShaderConstantATI(dst: int, value: FloatArray) -> None: ...

def glInitFragmentShaderATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
