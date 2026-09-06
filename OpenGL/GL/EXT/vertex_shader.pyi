"""OpenGL.GL.EXT.vertex_shader -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, ByteArray, DoubleArray, FloatArray, FloatArrayResult, IntArray, IntArrayResult, ShortArray, UByteArray, UByteArrayResult, UIntArray, UShortArray

from OpenGL.raw.GL._types import *

GL_CURRENT_VERTEX_EXT: int
GL_FULL_RANGE_EXT: int
GL_INVARIANT_DATATYPE_EXT: int
GL_INVARIANT_EXT: int
GL_INVARIANT_VALUE_EXT: int
GL_LOCAL_CONSTANT_DATATYPE_EXT: int
GL_LOCAL_CONSTANT_EXT: int
GL_LOCAL_CONSTANT_VALUE_EXT: int
GL_LOCAL_EXT: int
GL_MATRIX_EXT: int
GL_MAX_OPTIMIZED_VERTEX_SHADER_INSTRUCTIONS_EXT: int
GL_MAX_OPTIMIZED_VERTEX_SHADER_INVARIANTS_EXT: int
GL_MAX_OPTIMIZED_VERTEX_SHADER_LOCALS_EXT: int
GL_MAX_OPTIMIZED_VERTEX_SHADER_LOCAL_CONSTANTS_EXT: int
GL_MAX_OPTIMIZED_VERTEX_SHADER_VARIANTS_EXT: int
GL_MAX_VERTEX_SHADER_INSTRUCTIONS_EXT: int
GL_MAX_VERTEX_SHADER_INVARIANTS_EXT: int
GL_MAX_VERTEX_SHADER_LOCALS_EXT: int
GL_MAX_VERTEX_SHADER_LOCAL_CONSTANTS_EXT: int
GL_MAX_VERTEX_SHADER_VARIANTS_EXT: int
GL_MVP_MATRIX_EXT: int
GL_NEGATIVE_ONE_EXT: int
GL_NEGATIVE_W_EXT: int
GL_NEGATIVE_X_EXT: int
GL_NEGATIVE_Y_EXT: int
GL_NEGATIVE_Z_EXT: int
GL_NORMALIZED_RANGE_EXT: int
GL_ONE_EXT: int
GL_OP_ADD_EXT: int
GL_OP_CLAMP_EXT: int
GL_OP_CROSS_PRODUCT_EXT: int
GL_OP_DOT3_EXT: int
GL_OP_DOT4_EXT: int
GL_OP_EXP_BASE_2_EXT: int
GL_OP_FLOOR_EXT: int
GL_OP_FRAC_EXT: int
GL_OP_INDEX_EXT: int
GL_OP_LOG_BASE_2_EXT: int
GL_OP_MADD_EXT: int
GL_OP_MAX_EXT: int
GL_OP_MIN_EXT: int
GL_OP_MOV_EXT: int
GL_OP_MULTIPLY_MATRIX_EXT: int
GL_OP_MUL_EXT: int
GL_OP_NEGATE_EXT: int
GL_OP_POWER_EXT: int
GL_OP_RECIP_EXT: int
GL_OP_RECIP_SQRT_EXT: int
GL_OP_ROUND_EXT: int
GL_OP_SET_GE_EXT: int
GL_OP_SET_LT_EXT: int
GL_OP_SUB_EXT: int
GL_OUTPUT_COLOR0_EXT: int
GL_OUTPUT_COLOR1_EXT: int
GL_OUTPUT_FOG_EXT: int
GL_OUTPUT_TEXTURE_COORD0_EXT: int
GL_OUTPUT_TEXTURE_COORD10_EXT: int
GL_OUTPUT_TEXTURE_COORD11_EXT: int
GL_OUTPUT_TEXTURE_COORD12_EXT: int
GL_OUTPUT_TEXTURE_COORD13_EXT: int
GL_OUTPUT_TEXTURE_COORD14_EXT: int
GL_OUTPUT_TEXTURE_COORD15_EXT: int
GL_OUTPUT_TEXTURE_COORD16_EXT: int
GL_OUTPUT_TEXTURE_COORD17_EXT: int
GL_OUTPUT_TEXTURE_COORD18_EXT: int
GL_OUTPUT_TEXTURE_COORD19_EXT: int
GL_OUTPUT_TEXTURE_COORD1_EXT: int
GL_OUTPUT_TEXTURE_COORD20_EXT: int
GL_OUTPUT_TEXTURE_COORD21_EXT: int
GL_OUTPUT_TEXTURE_COORD22_EXT: int
GL_OUTPUT_TEXTURE_COORD23_EXT: int
GL_OUTPUT_TEXTURE_COORD24_EXT: int
GL_OUTPUT_TEXTURE_COORD25_EXT: int
GL_OUTPUT_TEXTURE_COORD26_EXT: int
GL_OUTPUT_TEXTURE_COORD27_EXT: int
GL_OUTPUT_TEXTURE_COORD28_EXT: int
GL_OUTPUT_TEXTURE_COORD29_EXT: int
GL_OUTPUT_TEXTURE_COORD2_EXT: int
GL_OUTPUT_TEXTURE_COORD30_EXT: int
GL_OUTPUT_TEXTURE_COORD31_EXT: int
GL_OUTPUT_TEXTURE_COORD3_EXT: int
GL_OUTPUT_TEXTURE_COORD4_EXT: int
GL_OUTPUT_TEXTURE_COORD5_EXT: int
GL_OUTPUT_TEXTURE_COORD6_EXT: int
GL_OUTPUT_TEXTURE_COORD7_EXT: int
GL_OUTPUT_TEXTURE_COORD8_EXT: int
GL_OUTPUT_TEXTURE_COORD9_EXT: int
GL_OUTPUT_VERTEX_EXT: int
GL_SCALAR_EXT: int
GL_VARIANT_ARRAY_EXT: int
GL_VARIANT_ARRAY_POINTER_EXT: int
GL_VARIANT_ARRAY_STRIDE_EXT: int
GL_VARIANT_ARRAY_TYPE_EXT: int
GL_VARIANT_DATATYPE_EXT: int
GL_VARIANT_EXT: int
GL_VARIANT_VALUE_EXT: int
GL_VECTOR_EXT: int
GL_VERTEX_SHADER_BINDING_EXT: int
GL_VERTEX_SHADER_EXT: int
GL_VERTEX_SHADER_INSTRUCTIONS_EXT: int
GL_VERTEX_SHADER_INVARIANTS_EXT: int
GL_VERTEX_SHADER_LOCALS_EXT: int
GL_VERTEX_SHADER_LOCAL_CONSTANTS_EXT: int
GL_VERTEX_SHADER_OPTIMIZED_EXT: int
GL_VERTEX_SHADER_VARIANTS_EXT: int
GL_W_EXT: int
GL_X_EXT: int
GL_Y_EXT: int
GL_ZERO_EXT: int
GL_Z_EXT: int

def glBeginVertexShaderEXT() -> None: ...
def glBindLightParameterEXT(light: int, value: int) -> int: ...
def glBindMaterialParameterEXT(face: int, value: int) -> int: ...
def glBindParameterEXT(value: int) -> int: ...
def glBindTexGenParameterEXT(unit: int, coord: int, value: int) -> int: ...
def glBindTextureUnitParameterEXT(unit: int, value: int) -> int: ...
def glBindVertexShaderEXT(id: int) -> None: ...
def glDeleteVertexShaderEXT(id: int) -> None: ...
def glDisableVariantClientStateEXT(id: int) -> None: ...
def glEnableVariantClientStateEXT(id: int) -> None: ...
def glEndVertexShaderEXT() -> None: ...
def glExtractComponentEXT(res: int, src: int, num: int) -> None: ...
def glGenSymbolsEXT(datatype: int, storagetype: int, range: int, components: int) -> int: ...
def glGenVertexShadersEXT(range: int) -> int: ...
def glGetInvariantBooleanvEXT(id: int, value: int, data: UByteArray | None = None) -> UByteArrayResult: ...
def glGetInvariantFloatvEXT(id: int, value: int, data: FloatArray | None = None) -> FloatArrayResult: ...
def glGetInvariantIntegervEXT(id: int, value: int, data: IntArray | None = None) -> IntArrayResult: ...
def glGetLocalConstantBooleanvEXT(id: int, value: int, data: UByteArray | None = None) -> UByteArrayResult: ...
def glGetLocalConstantFloatvEXT(id: int, value: int, data: FloatArray | None = None) -> FloatArrayResult: ...
def glGetLocalConstantIntegervEXT(id: int, value: int, data: IntArray | None = None) -> IntArrayResult: ...
def glGetVariantBooleanvEXT(id: int, value: int, data: UByteArray | None = None) -> UByteArrayResult: ...
def glGetVariantFloatvEXT(id: int, value: int, data: FloatArray | None = None) -> FloatArrayResult: ...
def glGetVariantIntegervEXT(id: int, value: int, data: IntArray | None = None) -> IntArrayResult: ...
def glGetVariantPointervEXT(id: int, value: int, data: AnyArray | None = None) -> AnyArrayResult: ...
def glInsertComponentEXT(res: int, src: int, num: int) -> None: ...
def glIsVariantEnabledEXT(id: int, cap: int) -> int: ...
def glSetInvariantEXT(id: int, type: int, addr: AnyArray) -> None: ...
def glSetLocalConstantEXT(id: int, type: int, addr: AnyArray) -> None: ...
def glShaderOp1EXT(op: int, res: int, arg1: int) -> None: ...
def glShaderOp2EXT(op: int, res: int, arg1: int, arg2: int) -> None: ...
def glShaderOp3EXT(op: int, res: int, arg1: int, arg2: int, arg3: int) -> None: ...
def glSwizzleEXT(res: int, in_: int, outX: int, outY: int, outZ: int, outW: int) -> None: ...
def glVariantPointerEXT(id: int, type: int, stride: int, addr: AnyArray) -> None: ...
def glVariantbvEXT(id: int, addr: ByteArray) -> None: ...
def glVariantdvEXT(id: int, addr: DoubleArray) -> None: ...
def glVariantfvEXT(id: int, addr: FloatArray) -> None: ...
def glVariantivEXT(id: int, addr: IntArray) -> None: ...
def glVariantsvEXT(id: int, addr: ShortArray) -> None: ...
def glVariantubvEXT(id: int, addr: UByteArray) -> None: ...
def glVariantuivEXT(id: int, addr: UIntArray) -> None: ...
def glVariantusvEXT(id: int, addr: UShortArray) -> None: ...
def glWriteMaskEXT(res: int, in_: int, outX: int, outY: int, outZ: int, outW: int) -> None: ...

def glInitVertexShaderEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
