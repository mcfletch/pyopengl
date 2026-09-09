"""OpenGL.GLU -- generated; regenerate with src/regenerate_c.py.

GLU is hand-maintained rather than registry-generated (it is not a Khronos
API), so this is emitted from the declarations in ``OpenGL/raw/GLU`` and
``OpenGL/GLU`` rather than from the registry.
"""

from collections.abc import Callable, Sequence
from typing import Any

from OpenGL.raw.GL._types import *

GLU_AUTO_LOAD_MATRIX: int
GLU_BEGIN: int
GLU_CCW: int
GLU_CULLING: int
GLU_CW: int
GLU_DISPLAY_MODE: int
GLU_DOMAIN_DISTANCE: int
GLU_EDGE_FLAG: int
GLU_END: int
GLU_ERROR: int
GLU_EXTENSIONS: int
GLU_EXTERIOR: int
GLU_FALSE: int
GLU_FILL: int
GLU_FLAT: int
GLU_INCOMPATIBLE_GL_VERSION: int
GLU_INSIDE: int
GLU_INTERIOR: int
GLU_INVALID_ENUM: int
GLU_INVALID_OPERATION: int
GLU_INVALID_VALUE: int
GLU_LINE: int
GLU_MAP1_TRIM_2: int
GLU_MAP1_TRIM_3: int
GLU_NONE: int
GLU_NURBS_BEGIN: int
GLU_NURBS_BEGIN_DATA: int
GLU_NURBS_BEGIN_DATA_EXT: int
GLU_NURBS_BEGIN_EXT: int
GLU_NURBS_COLOR: int
GLU_NURBS_COLOR_DATA: int
GLU_NURBS_COLOR_DATA_EXT: int
GLU_NURBS_COLOR_EXT: int
GLU_NURBS_END: int
GLU_NURBS_END_DATA: int
GLU_NURBS_END_DATA_EXT: int
GLU_NURBS_END_EXT: int
GLU_NURBS_ERROR: int
GLU_NURBS_ERROR1: int
GLU_NURBS_ERROR10: int
GLU_NURBS_ERROR11: int
GLU_NURBS_ERROR12: int
GLU_NURBS_ERROR13: int
GLU_NURBS_ERROR14: int
GLU_NURBS_ERROR15: int
GLU_NURBS_ERROR16: int
GLU_NURBS_ERROR17: int
GLU_NURBS_ERROR18: int
GLU_NURBS_ERROR19: int
GLU_NURBS_ERROR2: int
GLU_NURBS_ERROR20: int
GLU_NURBS_ERROR21: int
GLU_NURBS_ERROR22: int
GLU_NURBS_ERROR23: int
GLU_NURBS_ERROR24: int
GLU_NURBS_ERROR25: int
GLU_NURBS_ERROR26: int
GLU_NURBS_ERROR27: int
GLU_NURBS_ERROR28: int
GLU_NURBS_ERROR29: int
GLU_NURBS_ERROR3: int
GLU_NURBS_ERROR30: int
GLU_NURBS_ERROR31: int
GLU_NURBS_ERROR32: int
GLU_NURBS_ERROR33: int
GLU_NURBS_ERROR34: int
GLU_NURBS_ERROR35: int
GLU_NURBS_ERROR36: int
GLU_NURBS_ERROR37: int
GLU_NURBS_ERROR4: int
GLU_NURBS_ERROR5: int
GLU_NURBS_ERROR6: int
GLU_NURBS_ERROR7: int
GLU_NURBS_ERROR8: int
GLU_NURBS_ERROR9: int
GLU_NURBS_MODE: int
GLU_NURBS_MODE_EXT: int
GLU_NURBS_NORMAL: int
GLU_NURBS_NORMAL_DATA: int
GLU_NURBS_NORMAL_DATA_EXT: int
GLU_NURBS_NORMAL_EXT: int
GLU_NURBS_RENDERER: int
GLU_NURBS_RENDERER_EXT: int
GLU_NURBS_TESSELLATOR: int
GLU_NURBS_TESSELLATOR_EXT: int
GLU_NURBS_TEXTURE_COORD: int
GLU_NURBS_TEXTURE_COORD_DATA: int
GLU_NURBS_TEX_COORD_DATA_EXT: int
GLU_NURBS_TEX_COORD_EXT: int
GLU_NURBS_VERTEX: int
GLU_NURBS_VERTEX_DATA: int
GLU_NURBS_VERTEX_DATA_EXT: int
GLU_NURBS_VERTEX_EXT: int
GLU_OBJECT_PARAMETRIC_ERROR: int
GLU_OBJECT_PARAMETRIC_ERROR_EXT: int
GLU_OBJECT_PATH_LENGTH: int
GLU_OBJECT_PATH_LENGTH_EXT: int
GLU_OUTLINE_PATCH: int
GLU_OUTLINE_POLYGON: int
GLU_OUTSIDE: int
GLU_OUT_OF_MEMORY: int
GLU_PARAMETRIC_ERROR: int
GLU_PARAMETRIC_TOLERANCE: int
GLU_PATH_LENGTH: int
GLU_POINT: int
GLU_SAMPLING_METHOD: int
GLU_SAMPLING_TOLERANCE: int
GLU_SILHOUETTE: int
GLU_SMOOTH: int
GLU_TESS_BEGIN: int
GLU_TESS_BEGIN_DATA: int
GLU_TESS_BOUNDARY_ONLY: int
GLU_TESS_COMBINE: int
GLU_TESS_COMBINE_DATA: int
GLU_TESS_COORD_TOO_LARGE: int
GLU_TESS_EDGE_FLAG: int
GLU_TESS_EDGE_FLAG_DATA: int
GLU_TESS_END: int
GLU_TESS_END_DATA: int
GLU_TESS_ERROR: int
GLU_TESS_ERROR1: int
GLU_TESS_ERROR2: int
GLU_TESS_ERROR3: int
GLU_TESS_ERROR4: int
GLU_TESS_ERROR5: int
GLU_TESS_ERROR6: int
GLU_TESS_ERROR7: int
GLU_TESS_ERROR8: int
GLU_TESS_ERROR_DATA: int
GLU_TESS_MAX_COORD: int
GLU_TESS_MISSING_BEGIN_CONTOUR: int
GLU_TESS_MISSING_BEGIN_POLYGON: int
GLU_TESS_MISSING_END_CONTOUR: int
GLU_TESS_MISSING_END_POLYGON: int
GLU_TESS_NEED_COMBINE_CALLBACK: int
GLU_TESS_TOLERANCE: int
GLU_TESS_VERTEX: int
GLU_TESS_VERTEX_DATA: int
GLU_TESS_WINDING_ABS_GEQ_TWO: int
GLU_TESS_WINDING_NEGATIVE: int
GLU_TESS_WINDING_NONZERO: int
GLU_TESS_WINDING_ODD: int
GLU_TESS_WINDING_POSITIVE: int
GLU_TESS_WINDING_RULE: int
GLU_TRUE: int
GLU_UNKNOWN: int
GLU_U_STEP: int
GLU_VERSION: int
GLU_VERSION_1_1: int
GLU_VERSION_1_2: int
GLU_VERSION_1_3: int
GLU_VERTEX: int
GLU_V_STEP: int

def gluBeginCurve(nurb: Any) -> None: ...
def gluBeginPolygon(tess: Any) -> None: ...
def gluBeginSurface(nurb: Any) -> None: ...
def gluBeginTrim(nurb: Any) -> None: ...
def gluBuild1DMipmapLevels(target: int, internalFormat: int, width: int, format: int, type: int, level: int, base: int, max: int, data: Any) -> int: ...
def gluBuild1DMipmaps(target: int, internalFormat: int, width: int, format: int, type: int, data: Any) -> int: ...
def gluBuild2DMipmapLevels(target: int, internalFormat: int, width: int, height: int, format: int, type: int, level: int, base: int, max: int, data: Any) -> int: ...
def gluBuild2DMipmaps(target: int, internalFormat: int, width: int, height: int, format: int, type: int, data: Any) -> int: ...
def gluBuild3DMipmapLevels(target: int, internalFormat: int, width: int, height: int, depth: int, format: int, type: int, level: int, base: int, max: int, data: Any) -> int: ...
def gluBuild3DMipmaps(target: int, internalFormat: int, width: int, height: int, depth: int, format: int, type: int, data: Any) -> int: ...
def gluCheckExtension(extName: Any, extString: Any) -> Any: ...
def gluCylinder(quad: Any, base: float, top: float, height: float, slices: int, stacks: int) -> None: ...
def gluDeleteNurbsRenderer(nurb: Any) -> None: ...
def gluDeleteQuadric(quad: Any) -> None: ...
def gluDeleteTess(tess: Any) -> None: ...
def gluDisk(quad: Any, inner: float, outer: float, slices: int, loops: int) -> None: ...
def gluEndCurve(nurb: Any) -> None: ...
def gluEndPolygon(tess: Any) -> None: ...
def gluEndSurface(nurb: Any) -> None: ...
def gluEndTrim(nurb: Any) -> None: ...
def gluErrorString(error: int) -> Any: ...
def gluGetNurbsProperty(nurb: Any, property: Any, value: Any = ...) -> Any: ...
def gluGetString(name: int) -> Any: ...
def gluGetTessProperty(tess: Any, which: Any, data: Any = ...) -> Any: ...
def gluLoadSamplingMatrices(nurb: Any, model: Any, perspective: Any, view: Any) -> Any: ...
def gluLookAt(eyeX: float, eyeY: float, eyeZ: float, centerX: float, centerY: float, centerZ: float, upX: float, upY: float, upZ: float) -> None: ...
def gluNewNurbsRenderer() -> Any: ...
def gluNewQuadric() -> Any: ...
def gluNewTess() -> Any: ...
def gluNextContour(tess: Any, type: int) -> None: ...
def gluNurbsCallback(nurb: Any, which: Any, CallBackFunc: Any) -> Any: ...
def gluNurbsCallbackData(nurb: Any, userData: Any) -> Any: ...
def gluNurbsCallbackDataEXT(nurb: Any, userData: Any) -> Any: ...
def gluNurbsCurve(nurb: Any, knots: Any, control: Any, type: Any) -> Any: ...
def gluNurbsProperty(nurb: Any, property: int, value: float) -> None: ...
def gluNurbsSurface(nurb: Any, sKnots: Any, tKnots: Any, control: Any, type: Any) -> Any: ...
def gluOrtho2D(left: float, right: float, bottom: float, top: float) -> None: ...
def gluPartialDisk(quad: Any, inner: float, outer: float, slices: int, loops: int, start: float, sweep: float) -> None: ...
def gluPerspective(fovy: float, aspect: float, zNear: float, zFar: float) -> None: ...
def gluPickMatrix(x: Any, y: Any, delX: Any, delY: Any, viewport: Any) -> Any: ...
def gluProject(objX: Any, objY: Any, objZ: Any, model: Any = ..., proj: Any = ..., view: Any = ...) -> Any: ...
def gluPwlCurve(nurb: Any, data: Any, type: Any) -> Any: ...
def gluQuadricCallback(quadric: Any, which: Any = ..., function: Any = ...) -> Any: ...
def gluQuadricDrawStyle(quad: Any, draw: int) -> None: ...
def gluQuadricNormals(quad: Any, normal: int) -> None: ...
def gluQuadricOrientation(quad: Any, orientation: int) -> None: ...
def gluQuadricTexture(quad: Any, texture: int) -> None: ...
def gluScaleImage(format: int, wIn: int, hIn: int, typeIn: int, dataIn: Any, wOut: int, hOut: int, typeOut: int, dataOut: Any) -> int: ...
def gluSphere(quad: Any, radius: float, slices: int, stacks: int) -> None: ...
def gluTessBeginContour(tess: Any) -> None: ...
def gluTessBeginPolygon(tess: Any, data: Any) -> Any: ...
def gluTessCallback(tess: Any, which: Any, function: Any) -> Any: ...
def gluTessEndContour(tess: Any) -> None: ...
def gluTessEndPolygon(tess: Any) -> None: ...
def gluTessNormal(tess: Any, valueX: float, valueY: float, valueZ: float) -> None: ...
def gluTessProperty(tess: Any, which: int, data: float) -> None: ...
def gluTessVertex(tess: Any, location: Any, data: Any = ...) -> Any: ...
def gluUnProject(winX: Any, winY: Any, winZ: Any, model: Any = ..., proj: Any = ..., view: Any = ...) -> Any: ...
def gluUnProject4(winX: Any, winY: Any, winZ: Any, clipW: Any, model: Any = ..., proj: Any = ..., view: Any = ..., near: Any = ..., far: Any = ...) -> Any: ...
def glutCheckLoop() -> Any: ...
def glutCreateMenu(function: Callable[..., Any] | None) -> int: ...
def glutDestroyMenu(menu: int) -> Any: ...
def glutDestroyWindow(window: int) -> Any: ...
def glutInit(*args: Any) -> Sequence[Any]: ...
def glutSolidSierpinskiSponge(levels: int, offset: Any, scale: float) -> None: ...
def glutWireSierpinskiSponge(levels: int, offset: Any, scale: float) -> None: ...

def __getattr__(name: str) -> Any: ...
