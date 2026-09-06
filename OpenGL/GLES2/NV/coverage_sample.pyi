"""OpenGL.GLES2.NV.coverage_sample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_COVERAGE_ALL_FRAGMENTS_NV: int
GL_COVERAGE_ATTACHMENT_NV: int
GL_COVERAGE_AUTOMATIC_NV: int
GL_COVERAGE_BUFFERS_NV: int
GL_COVERAGE_BUFFER_BIT_NV: int
GL_COVERAGE_COMPONENT4_NV: int
GL_COVERAGE_COMPONENT_NV: int
GL_COVERAGE_EDGE_FRAGMENTS_NV: int
GL_COVERAGE_SAMPLES_NV: int

def glCoverageMaskNV(mask: bool) -> None: ...
def glCoverageOperationNV(operation: int) -> None: ...

def glInitCoverageSampleNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
