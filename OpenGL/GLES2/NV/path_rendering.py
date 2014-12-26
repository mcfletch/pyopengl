'''OpenGL extension NV.path_rendering

This module customises the behaviour of the 
OpenGL.raw.GLES2.NV.path_rendering to provide a more 
Python-friendly API

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/NV/path_rendering.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GLES2 import _types, _glgets
from OpenGL.raw.GLES2.NV.path_rendering import *
from OpenGL.raw.GLES2.NV.path_rendering import _EXTENSION_NAME

def glInitPathRenderingNV():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )

# INPUT glPathCommandsNV.commands size not checked against numCommands
# INPUT glPathCommandsNV.coords size not checked against 'numCoords,coordType'
glPathCommandsNV=wrapper.wrapper(glPathCommandsNV).setInputArraySize(
    'commands', None
).setInputArraySize(
    'coords', None
)
# INPUT glPathCoordsNV.coords size not checked against 'numCoords,coordType'
glPathCoordsNV=wrapper.wrapper(glPathCoordsNV).setInputArraySize(
    'coords', None
)
# INPUT glPathSubCommandsNV.commands size not checked against numCommands
# INPUT glPathSubCommandsNV.coords size not checked against 'numCoords,coordType'
glPathSubCommandsNV=wrapper.wrapper(glPathSubCommandsNV).setInputArraySize(
    'commands', None
).setInputArraySize(
    'coords', None
)
# INPUT glPathSubCoordsNV.coords size not checked against 'numCoords,coordType'
glPathSubCoordsNV=wrapper.wrapper(glPathSubCoordsNV).setInputArraySize(
    'coords', None
)
# INPUT glPathStringNV.pathString size not checked against length
glPathStringNV=wrapper.wrapper(glPathStringNV).setInputArraySize(
    'pathString', None
)
# INPUT glPathGlyphsNV.charcodes size not checked against 'numGlyphs,type,charcodes'
# INPUT glPathGlyphsNV.fontName size not checked against 'fontTarget,fontName'
glPathGlyphsNV=wrapper.wrapper(glPathGlyphsNV).setInputArraySize(
    'charcodes', None
).setInputArraySize(
    'fontName', None
)
# INPUT glPathGlyphRangeNV.fontName size not checked against 'fontTarget,fontName'
glPathGlyphRangeNV=wrapper.wrapper(glPathGlyphRangeNV).setInputArraySize(
    'fontName', None
)
# INPUT glWeightPathsNV.paths size not checked against numPaths
# INPUT glWeightPathsNV.weights size not checked against numPaths
glWeightPathsNV=wrapper.wrapper(glWeightPathsNV).setInputArraySize(
    'paths', None
).setInputArraySize(
    'weights', None
)
# INPUT glTransformPathNV.transformValues size not checked against 'transformType'
glTransformPathNV=wrapper.wrapper(glTransformPathNV).setInputArraySize(
    'transformValues', None
)
# INPUT glPathParameterivNV.value size not checked against 'pname'
glPathParameterivNV=wrapper.wrapper(glPathParameterivNV).setInputArraySize(
    'value', None
)
# INPUT glPathParameterfvNV.value size not checked against 'pname'
glPathParameterfvNV=wrapper.wrapper(glPathParameterfvNV).setInputArraySize(
    'value', None
)
# INPUT glPathDashArrayNV.dashArray size not checked against dashCount
glPathDashArrayNV=wrapper.wrapper(glPathDashArrayNV).setInputArraySize(
    'dashArray', None
)
# INPUT glStencilFillPathInstancedNV.paths size not checked against 'numPaths,pathNameType,paths'
# INPUT glStencilFillPathInstancedNV.transformValues size not checked against 'numPaths,transformType'
glStencilFillPathInstancedNV=wrapper.wrapper(glStencilFillPathInstancedNV).setInputArraySize(
    'paths', None
).setInputArraySize(
    'transformValues', None
)
# INPUT glStencilStrokePathInstancedNV.paths size not checked against 'numPaths,pathNameType,paths'
# INPUT glStencilStrokePathInstancedNV.transformValues size not checked against 'numPaths,transformType'
glStencilStrokePathInstancedNV=wrapper.wrapper(glStencilStrokePathInstancedNV).setInputArraySize(
    'paths', None
).setInputArraySize(
    'transformValues', None
)
# INPUT glCoverFillPathInstancedNV.paths size not checked against 'numPaths,pathNameType,paths'
# INPUT glCoverFillPathInstancedNV.transformValues size not checked against 'numPaths,transformType'
glCoverFillPathInstancedNV=wrapper.wrapper(glCoverFillPathInstancedNV).setInputArraySize(
    'paths', None
).setInputArraySize(
    'transformValues', None
)
# INPUT glCoverStrokePathInstancedNV.paths size not checked against 'numPaths,pathNameType,paths'
# INPUT glCoverStrokePathInstancedNV.transformValues size not checked against 'numPaths,transformType'
glCoverStrokePathInstancedNV=wrapper.wrapper(glCoverStrokePathInstancedNV).setInputArraySize(
    'paths', None
).setInputArraySize(
    'transformValues', None
)
glGetPathParameterivNV=wrapper.wrapper(glGetPathParameterivNV).setOutput(
    'value',size=(4,),orPassIn=True
)
glGetPathParameterfvNV=wrapper.wrapper(glGetPathParameterfvNV).setOutput(
    'value',size=(4,),orPassIn=True
)
glGetPathCommandsNV=wrapper.wrapper(glGetPathCommandsNV).setOutput(
    'commands',size=_glgets._glget_size_mapping,pnameArg='path',orPassIn=True
)
glGetPathCoordsNV=wrapper.wrapper(glGetPathCoordsNV).setOutput(
    'coords',size=_glgets._glget_size_mapping,pnameArg='path',orPassIn=True
)
glGetPathDashArrayNV=wrapper.wrapper(glGetPathDashArrayNV).setOutput(
    'dashArray',size=_glgets._glget_size_mapping,pnameArg='path',orPassIn=True
)
# OUTPUT glGetPathMetricsNV.metrics COMPSIZE(metricQueryMask, numPaths, stride) 
# INPUT glGetPathMetricsNV.paths size not checked against 'numPaths,pathNameType,paths'
glGetPathMetricsNV=wrapper.wrapper(glGetPathMetricsNV).setInputArraySize(
    'paths', None
)
# OUTPUT glGetPathMetricRangeNV.metrics COMPSIZE(metricQueryMask, numPaths, stride) 
# INPUT glGetPathSpacingNV.paths size not checked against 'numPaths,pathNameType,paths'
# OUTPUT glGetPathSpacingNV.returnedSpacing COMPSIZE(pathListMode, numPaths) 
glGetPathSpacingNV=wrapper.wrapper(glGetPathSpacingNV).setInputArraySize(
    'paths', None
)
glPointAlongPathNV=wrapper.wrapper(glPointAlongPathNV).setOutput(
    'tangentX',size=(1,),orPassIn=True
).setOutput(
    'tangentY',size=(1,),orPassIn=True
).setOutput(
    'x',size=(1,),orPassIn=True
).setOutput(
    'y',size=(1,),orPassIn=True
)
# INPUT glPathColorGenNV.coeffs size not checked against 'genMode,colorFormat'
glPathColorGenNV=wrapper.wrapper(glPathColorGenNV).setInputArraySize(
    'coeffs', None
)
# INPUT glPathTexGenNV.coeffs size not checked against 'genMode,components'
glPathTexGenNV=wrapper.wrapper(glPathTexGenNV).setInputArraySize(
    'coeffs', None
)
glGetPathColorGenivNV=wrapper.wrapper(glGetPathColorGenivNV).setOutput(
    'value',size=_glgets._glget_size_mapping,pnameArg='pname',orPassIn=True
)
glGetPathColorGenfvNV=wrapper.wrapper(glGetPathColorGenfvNV).setOutput(
    'value',size=_glgets._glget_size_mapping,pnameArg='pname',orPassIn=True
)
glGetPathTexGenivNV=wrapper.wrapper(glGetPathTexGenivNV).setOutput(
    'value',size=_glgets._glget_size_mapping,pnameArg='pname',orPassIn=True
)
glGetPathTexGenfvNV=wrapper.wrapper(glGetPathTexGenfvNV).setOutput(
    'value',size=_glgets._glget_size_mapping,pnameArg='pname',orPassIn=True
)
### END AUTOGENERATED SECTION