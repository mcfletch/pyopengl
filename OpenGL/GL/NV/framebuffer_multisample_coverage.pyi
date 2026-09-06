"""OpenGL.GL.NV.framebuffer_multisample_coverage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_MULTISAMPLE_COVERAGE_MODES_NV: int
GL_MULTISAMPLE_COVERAGE_MODES_NV: int
GL_RENDERBUFFER_COLOR_SAMPLES_NV: int
GL_RENDERBUFFER_COVERAGE_SAMPLES_NV: int

def glRenderbufferStorageMultisampleCoverageNV(target: int, coverageSamples: int, colorSamples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferMultisampleCoverageNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
