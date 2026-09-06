"""OpenGL.GL.NV.blend_equation_advanced -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BLEND_OVERLAP_NV: int
GL_BLEND_PREMULTIPLIED_SRC_NV: int
GL_BLUE_NV: int
GL_COLORBURN_NV: int
GL_COLORDODGE_NV: int
GL_CONJOINT_NV: int
GL_CONTRAST_NV: int
GL_DARKEN_NV: int
GL_DIFFERENCE_NV: int
GL_DISJOINT_NV: int
GL_DST_ATOP_NV: int
GL_DST_IN_NV: int
GL_DST_NV: int
GL_DST_OUT_NV: int
GL_DST_OVER_NV: int
GL_EXCLUSION_NV: int
GL_GREEN_NV: int
GL_HARDLIGHT_NV: int
GL_HARDMIX_NV: int
GL_HSL_COLOR_NV: int
GL_HSL_HUE_NV: int
GL_HSL_LUMINOSITY_NV: int
GL_HSL_SATURATION_NV: int
GL_INVERT: int
GL_INVERT_OVG_NV: int
GL_INVERT_RGB_NV: int
GL_LIGHTEN_NV: int
GL_LINEARBURN_NV: int
GL_LINEARDODGE_NV: int
GL_LINEARLIGHT_NV: int
GL_MINUS_CLAMPED_NV: int
GL_MINUS_NV: int
GL_MULTIPLY_NV: int
GL_OVERLAY_NV: int
GL_PINLIGHT_NV: int
GL_PLUS_CLAMPED_ALPHA_NV: int
GL_PLUS_CLAMPED_NV: int
GL_PLUS_DARKER_NV: int
GL_PLUS_NV: int
GL_RED_NV: int
GL_SCREEN_NV: int
GL_SOFTLIGHT_NV: int
GL_SRC_ATOP_NV: int
GL_SRC_IN_NV: int
GL_SRC_NV: int
GL_SRC_OUT_NV: int
GL_SRC_OVER_NV: int
GL_UNCORRELATED_NV: int
GL_VIVIDLIGHT_NV: int
GL_XOR_NV: int
GL_ZERO: int

def glBlendBarrierNV() -> None: ...
def glBlendParameteriNV(pname: int, value: int) -> None: ...

def glInitBlendEquationAdvancedNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
