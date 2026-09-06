"""OpenGL.GL.ARB.geometry_shader4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_ATTACHMENT_LAYERED_ARB: int
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LAYER: int
GL_FRAMEBUFFER_INCOMPLETE_LAYER_COUNT_ARB: int
GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS_ARB: int
GL_GEOMETRY_INPUT_TYPE_ARB: int
GL_GEOMETRY_OUTPUT_TYPE_ARB: int
GL_GEOMETRY_SHADER_ARB: int
GL_GEOMETRY_VERTICES_OUT_ARB: int
GL_LINES_ADJACENCY_ARB: int
GL_LINE_STRIP_ADJACENCY_ARB: int
GL_MAX_GEOMETRY_OUTPUT_VERTICES_ARB: int
GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS_ARB: int
GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS_ARB: int
GL_MAX_GEOMETRY_UNIFORM_COMPONENTS_ARB: int
GL_MAX_GEOMETRY_VARYING_COMPONENTS_ARB: int
GL_MAX_VARYING_COMPONENTS: int
GL_MAX_VERTEX_VARYING_COMPONENTS_ARB: int
GL_PROGRAM_POINT_SIZE_ARB: int
GL_TRIANGLES_ADJACENCY_ARB: int
GL_TRIANGLE_STRIP_ADJACENCY_ARB: int

def glFramebufferTextureARB(target: int, attachment: int, texture: int, level: int) -> None: ...
def glFramebufferTextureFaceARB(target: int, attachment: int, texture: int, level: int, face: int) -> None: ...
def glFramebufferTextureLayerARB(target: int, attachment: int, texture: int, level: int, layer: int) -> None: ...
def glProgramParameteriARB(program: int, pname: int, value: int) -> None: ...

def glInitGeometryShader4ARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
