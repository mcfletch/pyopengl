'''OpenGL extension VERSION.GL_4_5

This module customises the behaviour of the 
OpenGL.raw.GL.VERSION.GL_4_5 to provide a more 
Python-friendly API

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/VERSION/GL_4_5.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.VERSION.GL_4_5 import *
from OpenGL.raw.GL.VERSION.GL_4_5 import _EXTENSION_NAME

def glInitGl45VERSION():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )

# INPUT glCreateTransformFeedbacks.ids size not checked against n
glCreateTransformFeedbacks=wrapper.wrapper(glCreateTransformFeedbacks).setInputArraySize(
    'ids', None
)
# INPUT glCreateBuffers.buffers size not checked against n
glCreateBuffers=wrapper.wrapper(glCreateBuffers).setInputArraySize(
    'buffers', None
)
# INPUT glNamedBufferStorage.data size not checked against size
glNamedBufferStorage=wrapper.wrapper(glNamedBufferStorage).setInputArraySize(
    'data', None
)
# INPUT glNamedBufferData.data size not checked against size
glNamedBufferData=wrapper.wrapper(glNamedBufferData).setInputArraySize(
    'data', None
)
# INPUT glNamedBufferSubData.data size not checked against size
glNamedBufferSubData=wrapper.wrapper(glNamedBufferSubData).setInputArraySize(
    'data', None
)
# INPUT glClearNamedBufferData.data size not checked against 'format,type'
glClearNamedBufferData=wrapper.wrapper(glClearNamedBufferData).setInputArraySize(
    'data', None
)
# INPUT glClearNamedBufferSubData.data size not checked against 'format,type'
glClearNamedBufferSubData=wrapper.wrapper(glClearNamedBufferSubData).setInputArraySize(
    'data', None
)
glGetNamedBufferPointerv=wrapper.wrapper(glGetNamedBufferPointerv).setInputArraySize(
    'params', 1
)
# INPUT glGetNamedBufferSubData.data size not checked against size
glGetNamedBufferSubData=wrapper.wrapper(glGetNamedBufferSubData).setInputArraySize(
    'data', None
)
# INPUT glCreateFramebuffers.framebuffers size not checked against n
glCreateFramebuffers=wrapper.wrapper(glCreateFramebuffers).setInputArraySize(
    'framebuffers', None
)
# INPUT glNamedFramebufferDrawBuffers.bufs size not checked against n
glNamedFramebufferDrawBuffers=wrapper.wrapper(glNamedFramebufferDrawBuffers).setInputArraySize(
    'bufs', None
)
# INPUT glInvalidateNamedFramebufferData.attachments size not checked against numAttachments
glInvalidateNamedFramebufferData=wrapper.wrapper(glInvalidateNamedFramebufferData).setInputArraySize(
    'attachments', None
)
# INPUT glInvalidateNamedFramebufferSubData.attachments size not checked against numAttachments
glInvalidateNamedFramebufferSubData=wrapper.wrapper(glInvalidateNamedFramebufferSubData).setInputArraySize(
    'attachments', None
)
# INPUT glClearNamedFramebufferiv.value size not checked against 'buffer'
glClearNamedFramebufferiv=wrapper.wrapper(glClearNamedFramebufferiv).setInputArraySize(
    'value', None
)
# INPUT glClearNamedFramebufferuiv.value size not checked against 'buffer'
glClearNamedFramebufferuiv=wrapper.wrapper(glClearNamedFramebufferuiv).setInputArraySize(
    'value', None
)
# INPUT glClearNamedFramebufferfv.value size not checked against 'buffer'
glClearNamedFramebufferfv=wrapper.wrapper(glClearNamedFramebufferfv).setInputArraySize(
    'value', None
)
# INPUT glCreateRenderbuffers.renderbuffers size not checked against n
glCreateRenderbuffers=wrapper.wrapper(glCreateRenderbuffers).setInputArraySize(
    'renderbuffers', None
)
# INPUT glCreateTextures.textures size not checked against n
glCreateTextures=wrapper.wrapper(glCreateTextures).setInputArraySize(
    'textures', None
)
# INPUT glCompressedTextureSubImage1D.data size not checked against imageSize
glCompressedTextureSubImage1D=wrapper.wrapper(glCompressedTextureSubImage1D).setInputArraySize(
    'data', None
)
# INPUT glCompressedTextureSubImage2D.data size not checked against imageSize
glCompressedTextureSubImage2D=wrapper.wrapper(glCompressedTextureSubImage2D).setInputArraySize(
    'data', None
)
# INPUT glCompressedTextureSubImage3D.data size not checked against imageSize
glCompressedTextureSubImage3D=wrapper.wrapper(glCompressedTextureSubImage3D).setInputArraySize(
    'data', None
)
# INPUT glTextureParameterfv.param size not checked against 'pname'
glTextureParameterfv=wrapper.wrapper(glTextureParameterfv).setInputArraySize(
    'param', None
)
# INPUT glTextureParameterIiv.params size not checked against 'pname'
glTextureParameterIiv=wrapper.wrapper(glTextureParameterIiv).setInputArraySize(
    'params', None
)
# INPUT glTextureParameterIuiv.params size not checked against 'pname'
glTextureParameterIuiv=wrapper.wrapper(glTextureParameterIuiv).setInputArraySize(
    'params', None
)
# INPUT glTextureParameteriv.param size not checked against 'pname'
glTextureParameteriv=wrapper.wrapper(glTextureParameteriv).setInputArraySize(
    'param', None
)
# INPUT glGetTextureImage.pixels size not checked against bufSize
glGetTextureImage=wrapper.wrapper(glGetTextureImage).setInputArraySize(
    'pixels', None
)
# INPUT glGetCompressedTextureImage.pixels size not checked against bufSize
glGetCompressedTextureImage=wrapper.wrapper(glGetCompressedTextureImage).setInputArraySize(
    'pixels', None
)
# INPUT glCreateVertexArrays.arrays size not checked against n
glCreateVertexArrays=wrapper.wrapper(glCreateVertexArrays).setInputArraySize(
    'arrays', None
)
# INPUT glVertexArrayVertexBuffers.buffers size not checked against count
# INPUT glVertexArrayVertexBuffers.offsets size not checked against count
# INPUT glVertexArrayVertexBuffers.strides size not checked against count
glVertexArrayVertexBuffers=wrapper.wrapper(glVertexArrayVertexBuffers).setInputArraySize(
    'buffers', None
).setInputArraySize(
    'offsets', None
).setInputArraySize(
    'strides', None
)
# INPUT glCreateSamplers.samplers size not checked against n
glCreateSamplers=wrapper.wrapper(glCreateSamplers).setInputArraySize(
    'samplers', None
)
# INPUT glCreateProgramPipelines.pipelines size not checked against n
glCreateProgramPipelines=wrapper.wrapper(glCreateProgramPipelines).setInputArraySize(
    'pipelines', None
)
# INPUT glCreateQueries.ids size not checked against n
glCreateQueries=wrapper.wrapper(glCreateQueries).setInputArraySize(
    'ids', None
)
# INPUT glGetTextureSubImage.pixels size not checked against bufSize
glGetTextureSubImage=wrapper.wrapper(glGetTextureSubImage).setInputArraySize(
    'pixels', None
)
# INPUT glGetCompressedTextureSubImage.pixels size not checked against bufSize
glGetCompressedTextureSubImage=wrapper.wrapper(glGetCompressedTextureSubImage).setInputArraySize(
    'pixels', None
)
# INPUT glGetnCompressedTexImage.pixels size not checked against bufSize
glGetnCompressedTexImage=wrapper.wrapper(glGetnCompressedTexImage).setInputArraySize(
    'pixels', None
)
# INPUT glGetnTexImage.pixels size not checked against bufSize
glGetnTexImage=wrapper.wrapper(glGetnTexImage).setInputArraySize(
    'pixels', None
)
# INPUT glReadnPixels.data size not checked against bufSize
glReadnPixels=wrapper.wrapper(glReadnPixels).setInputArraySize(
    'data', None
)
# INPUT glGetnMapdv.v size not checked against 'bufSize'
glGetnMapdv=wrapper.wrapper(glGetnMapdv).setInputArraySize(
    'v', None
)
# INPUT glGetnPixelMapfv.values size not checked against 'bufSize'
glGetnPixelMapfv=wrapper.wrapper(glGetnPixelMapfv).setInputArraySize(
    'values', None
)
# INPUT glGetnPolygonStipple.pattern size not checked against bufSize
glGetnPolygonStipple=wrapper.wrapper(glGetnPolygonStipple).setInputArraySize(
    'pattern', None
)
# INPUT glGetnColorTable.table size not checked against bufSize
glGetnColorTable=wrapper.wrapper(glGetnColorTable).setInputArraySize(
    'table', None
)
# INPUT glGetnConvolutionFilter.image size not checked against bufSize
glGetnConvolutionFilter=wrapper.wrapper(glGetnConvolutionFilter).setInputArraySize(
    'image', None
)
# INPUT glGetnSeparableFilter.column size not checked against columnBufSize
# INPUT glGetnSeparableFilter.row size not checked against rowBufSize
glGetnSeparableFilter=wrapper.wrapper(glGetnSeparableFilter).setInputArraySize(
    'column', None
).setInputArraySize(
    'row', None
).setInputArraySize(
    'span', 0
)
# INPUT glGetnHistogram.values size not checked against bufSize
glGetnHistogram=wrapper.wrapper(glGetnHistogram).setInputArraySize(
    'values', None
)
# INPUT glGetnMinmax.values size not checked against bufSize
glGetnMinmax=wrapper.wrapper(glGetnMinmax).setInputArraySize(
    'values', None
)
### END AUTOGENERATED SECTION
