"""OpenGL.GL.NV.geometry_program4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_ATTACHMENT_LAYERED_EXT: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LAYER_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_LAYER_COUNT_EXT: int
GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS_EXT: int
GL_GEOMETRY_INPUT_TYPE_EXT: int
GL_GEOMETRY_OUTPUT_TYPE_EXT: int
GL_GEOMETRY_PROGRAM_NV: int
GL_GEOMETRY_VERTICES_OUT_EXT: int
GL_LINES_ADJACENCY_EXT: int
GL_LINE_STRIP_ADJACENCY_EXT: int
GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS_EXT: int
GL_MAX_PROGRAM_OUTPUT_VERTICES_NV: int
GL_MAX_PROGRAM_TOTAL_OUTPUT_COMPONENTS_NV: int
GL_PROGRAM_POINT_SIZE_EXT: int
GL_TRIANGLES_ADJACENCY_EXT: int
GL_TRIANGLE_STRIP_ADJACENCY_EXT: int

def glFramebufferTextureEXT(target: int, attachment: int, texture: int, level: int) -> None: ...
def glFramebufferTextureFaceEXT(target: int, attachment: int, texture: int, level: int, face: int) -> None: ...
def glFramebufferTextureLayerEXT(target: int, attachment: int, texture: int, level: int, layer: int) -> None: ...
def glProgramVertexLimitNV(target: int, limit: int) -> None: ...

def glInitGeometryProgram4NV() -> bool: ...

def __getattr__(name: str) -> Any: ...
