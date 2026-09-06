"""OpenGL.GL.ARB.imaging -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_BLEND_COLOR: int
GL_BLEND_EQUATION: int
GL_COLOR_MATRIX: int
GL_COLOR_MATRIX_STACK_DEPTH: int
GL_COLOR_TABLE: int
GL_COLOR_TABLE_ALPHA_SIZE: int
GL_COLOR_TABLE_BIAS: int
GL_COLOR_TABLE_BLUE_SIZE: int
GL_COLOR_TABLE_FORMAT: int
GL_COLOR_TABLE_GREEN_SIZE: int
GL_COLOR_TABLE_INTENSITY_SIZE: int
GL_COLOR_TABLE_LUMINANCE_SIZE: int
GL_COLOR_TABLE_RED_SIZE: int
GL_COLOR_TABLE_SCALE: int
GL_COLOR_TABLE_WIDTH: int
GL_CONSTANT_ALPHA: int
GL_CONSTANT_BORDER: int
GL_CONSTANT_COLOR: int
GL_CONVOLUTION_1D: int
GL_CONVOLUTION_2D: int
GL_CONVOLUTION_BORDER_COLOR: int
GL_CONVOLUTION_BORDER_MODE: int
GL_CONVOLUTION_FILTER_BIAS: int
GL_CONVOLUTION_FILTER_SCALE: int
GL_CONVOLUTION_FORMAT: int
GL_CONVOLUTION_HEIGHT: int
GL_CONVOLUTION_WIDTH: int
GL_FUNC_ADD: int
GL_FUNC_REVERSE_SUBTRACT: int
GL_FUNC_SUBTRACT: int
GL_HISTOGRAM: int
GL_HISTOGRAM_ALPHA_SIZE: int
GL_HISTOGRAM_BLUE_SIZE: int
GL_HISTOGRAM_FORMAT: int
GL_HISTOGRAM_GREEN_SIZE: int
GL_HISTOGRAM_LUMINANCE_SIZE: int
GL_HISTOGRAM_RED_SIZE: int
GL_HISTOGRAM_SINK: int
GL_HISTOGRAM_WIDTH: int
GL_MAX: int
GL_MAX_COLOR_MATRIX_STACK_DEPTH: int
GL_MAX_CONVOLUTION_HEIGHT: int
GL_MAX_CONVOLUTION_WIDTH: int
GL_MIN: int
GL_MINMAX: int
GL_MINMAX_FORMAT: int
GL_MINMAX_SINK: int
GL_ONE_MINUS_CONSTANT_ALPHA: int
GL_ONE_MINUS_CONSTANT_COLOR: int
GL_POST_COLOR_MATRIX_ALPHA_BIAS: int
GL_POST_COLOR_MATRIX_ALPHA_SCALE: int
GL_POST_COLOR_MATRIX_BLUE_BIAS: int
GL_POST_COLOR_MATRIX_BLUE_SCALE: int
GL_POST_COLOR_MATRIX_COLOR_TABLE: int
GL_POST_COLOR_MATRIX_GREEN_BIAS: int
GL_POST_COLOR_MATRIX_GREEN_SCALE: int
GL_POST_COLOR_MATRIX_RED_BIAS: int
GL_POST_COLOR_MATRIX_RED_SCALE: int
GL_POST_CONVOLUTION_ALPHA_BIAS: int
GL_POST_CONVOLUTION_ALPHA_SCALE: int
GL_POST_CONVOLUTION_BLUE_BIAS: int
GL_POST_CONVOLUTION_BLUE_SCALE: int
GL_POST_CONVOLUTION_COLOR_TABLE: int
GL_POST_CONVOLUTION_GREEN_BIAS: int
GL_POST_CONVOLUTION_GREEN_SCALE: int
GL_POST_CONVOLUTION_RED_BIAS: int
GL_POST_CONVOLUTION_RED_SCALE: int
GL_PROXY_COLOR_TABLE: int
GL_PROXY_HISTOGRAM: int
GL_PROXY_POST_COLOR_MATRIX_COLOR_TABLE: int
GL_PROXY_POST_CONVOLUTION_COLOR_TABLE: int
GL_REDUCE: int
GL_REPLICATE_BORDER: int
GL_SEPARABLE_2D: int
GL_TABLE_TOO_LARGE: int

def glBlendColor(red: float, green: float, blue: float, alpha: float) -> None: ...
def glBlendEquation(mode: int) -> None: ...
def glColorSubTable(target: int, start: int, count: int, format: int, type: int, data: AnyArray) -> None: ...
def glColorTable(target: int, internalformat: int, width: int, format: int, type: int, table: AnyArray) -> None: ...
def glColorTableParameterfv(target: int, pname: int, params: FloatArray) -> None: ...
def glColorTableParameteriv(target: int, pname: int, params: IntArray) -> None: ...
def glConvolutionFilter1D(target: int, internalformat: int, width: int, format: int, type: int, image: AnyArray) -> None: ...
def glConvolutionFilter2D(target: int, internalformat: int, width: int, height: int, format: int, type: int, image: AnyArray) -> None: ...
def glConvolutionParameterf(target: int, pname: int, params: float) -> None: ...
def glConvolutionParameterfv(target: int, pname: int, params: FloatArray) -> None: ...
def glConvolutionParameteri(target: int, pname: int, params: int) -> None: ...
def glConvolutionParameteriv(target: int, pname: int, params: IntArray) -> None: ...
def glCopyColorSubTable(target: int, start: int, x: int, y: int, width: int) -> None: ...
def glCopyColorTable(target: int, internalformat: int, x: int, y: int, width: int) -> None: ...
def glCopyConvolutionFilter1D(target: int, internalformat: int, x: int, y: int, width: int) -> None: ...
def glCopyConvolutionFilter2D(target: int, internalformat: int, x: int, y: int, width: int, height: int) -> None: ...
def glGetColorTable(target: int, format: int, type: int, table: AnyArray | None = None) -> AnyArrayResult: ...
def glGetColorTableParameterfv(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetColorTableParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetConvolutionFilter(target: int, format: int, type: int, image: AnyArray | None = None) -> AnyArrayResult: ...
def glGetConvolutionParameterfv(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetConvolutionParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetHistogram(target: int, reset: bool, format: int, type: int, values: AnyArray | None = None) -> AnyArrayResult: ...
def glGetHistogramParameterfv(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetHistogramParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetMinmax(target: int, reset: bool, format: int, type: int, values: AnyArray | None = None) -> AnyArrayResult: ...
def glGetMinmaxParameterfv(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetMinmaxParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetSeparableFilter(target: int, format: int, type: int, row: AnyArray | None = None, column: AnyArray | None = None, span: AnyArray | None = None) -> tuple[AnyArrayResult, AnyArrayResult, AnyArrayResult]: ...
def glHistogram(target: int, width: int, internalformat: int, sink: bool) -> None: ...
def glMinmax(target: int, internalformat: int, sink: bool) -> None: ...
def glResetHistogram(target: int) -> None: ...
def glResetMinmax(target: int) -> None: ...
def glSeparableFilter2D(target: int, internalformat: int, width: int, height: int, format: int, type: int, row: AnyArray, column: AnyArray) -> None: ...

def glInitImagingARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
