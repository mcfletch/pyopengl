"""OpenGL.GL.VERSION.GL_3_2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, FloatArray, FloatArrayResult, Int64Array, Int64ArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_ALREADY_SIGNALED: int
GL_CONDITION_SATISFIED: int
GL_CONTEXT_COMPATIBILITY_PROFILE_BIT: int
GL_CONTEXT_CORE_PROFILE_BIT: int
GL_CONTEXT_PROFILE_MASK: int
GL_DEPTH_CLAMP: int
GL_FIRST_VERTEX_CONVENTION: int
GL_FRAMEBUFFER_ATTACHMENT_LAYERED: int
GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS: int
GL_GEOMETRY_INPUT_TYPE: int
GL_GEOMETRY_OUTPUT_TYPE: int
GL_GEOMETRY_SHADER: int
GL_GEOMETRY_VERTICES_OUT: int
GL_INT_SAMPLER_2D_MULTISAMPLE: int
GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: int
GL_LAST_VERTEX_CONVENTION: int
GL_LINES_ADJACENCY: int
GL_LINE_STRIP_ADJACENCY: int
GL_MAX_COLOR_TEXTURE_SAMPLES: int
GL_MAX_DEPTH_TEXTURE_SAMPLES: int
GL_MAX_FRAGMENT_INPUT_COMPONENTS: int
GL_MAX_GEOMETRY_INPUT_COMPONENTS: int
GL_MAX_GEOMETRY_OUTPUT_COMPONENTS: int
GL_MAX_GEOMETRY_OUTPUT_VERTICES: int
GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS: int
GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS: int
GL_MAX_GEOMETRY_UNIFORM_COMPONENTS: int
GL_MAX_INTEGER_SAMPLES: int
GL_MAX_SAMPLE_MASK_WORDS: int
GL_MAX_SERVER_WAIT_TIMEOUT: int
GL_MAX_VERTEX_OUTPUT_COMPONENTS: int
GL_OBJECT_TYPE: int
GL_PROGRAM_POINT_SIZE: int
GL_PROVOKING_VERTEX: int
GL_PROXY_TEXTURE_2D_MULTISAMPLE: int
GL_PROXY_TEXTURE_2D_MULTISAMPLE_ARRAY: int
GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION: int
GL_SAMPLER_2D_MULTISAMPLE: int
GL_SAMPLER_2D_MULTISAMPLE_ARRAY: int
GL_SAMPLE_MASK: int
GL_SAMPLE_MASK_VALUE: int
GL_SAMPLE_POSITION: int
GL_SIGNALED: int
GL_SYNC_CONDITION: int
GL_SYNC_FENCE: int
GL_SYNC_FLAGS: int
GL_SYNC_FLUSH_COMMANDS_BIT: int
GL_SYNC_GPU_COMMANDS_COMPLETE: int
GL_SYNC_STATUS: int
GL_TEXTURE_2D_MULTISAMPLE: int
GL_TEXTURE_2D_MULTISAMPLE_ARRAY: int
GL_TEXTURE_BINDING_2D_MULTISAMPLE: int
GL_TEXTURE_BINDING_2D_MULTISAMPLE_ARRAY: int
GL_TEXTURE_CUBE_MAP_SEAMLESS: int
GL_TEXTURE_FIXED_SAMPLE_LOCATIONS: int
GL_TEXTURE_SAMPLES: int
GL_TIMEOUT_EXPIRED: int
GL_TIMEOUT_IGNORED: int
GL_TRIANGLES_ADJACENCY: int
GL_TRIANGLE_STRIP_ADJACENCY: int
GL_UNSIGNALED: int
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: int
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: int
GL_WAIT_FAILED: int

def glClientWaitSync(sync: Any, flags: int, timeout: int) -> int: ...
def glDeleteSync(sync: Any) -> None: ...
def glDrawElementsBaseVertex(mode: int, count: int, type: int, indices: AnyArray, basevertex: int) -> None: ...
def glDrawElementsInstancedBaseVertex(mode: int, count: int, type: int, indices: AnyArray, instancecount: int, basevertex: int) -> None: ...
def glDrawRangeElementsBaseVertex(mode: int, start: int, end: int, count: int, type: int, indices: AnyArray, basevertex: int) -> None: ...
def glFenceSync(condition: int, flags: int) -> Any: ...
def glFramebufferTexture(target: int, attachment: int, texture: int, level: int) -> None: ...
def glGetBufferParameteri64v(target: int, pname: int, params: Int64Array | None = None) -> Int64ArrayResult: ...
def glGetInteger64i_v(target: int, index: int, data: Int64Array | None = None) -> Int64ArrayResult: ...
def glGetInteger64v(pname: int, data: Int64Array | None = None) -> Int64ArrayResult: ...
def glGetMultisamplefv(pname: int, index: int, val: FloatArray | None = None) -> FloatArrayResult: ...
def glGetSynciv(sync: Any, pname: int, count: int, length: IntArray | None = None, values: IntArray | None = None) -> tuple[IntArrayResult, IntArrayResult]: ...
def glIsSync(sync: Any) -> int: ...
def glMultiDrawElementsBaseVertex(mode: int, count: IntArray, type: int, indices: AnyArray, drawcount: int, basevertex: IntArray) -> None: ...
def glProvokingVertex(mode: int) -> None: ...
def glSampleMaski(maskNumber: int, mask: int) -> None: ...
def glTexImage2DMultisample(target: int, samples: int, internalformat: int, width: int, height: int, fixedsamplelocations: int) -> None: ...
def glTexImage3DMultisample(target: int, samples: int, internalformat: int, width: int, height: int, depth: int, fixedsamplelocations: int) -> None: ...
def glWaitSync(sync: Any, flags: int, timeout: int) -> None: ...

def glInitGl32VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
