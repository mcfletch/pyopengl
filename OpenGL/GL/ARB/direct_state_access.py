'''OpenGL extension ARB.direct_state_access

This module customises the behaviour of the 
OpenGL.raw.GL.ARB.direct_state_access to provide a more 
Python-friendly API

Overview (from the spec)
	
	In unextended OpenGL, most mutation of state contained in objects is through
	an indirection known as a binding. Objects are attached to a context (either
	directly or indirectly via a container) and then commands to modify or
	query their state are issued on that context, indirecting through its
	attachments and into the underlying object. This is known as `bind-to-edit'.
	
	This extension derives from the GL_EXT_direct_state_access extension, which
	added accessors for most state on most objects, allowing it to be queried
	and modified without the object needing to be bound to a context. In cases
	where a single property of an object is to be modified, directly accessing
	its state can be more efficient than binding the object to the context and
	then indirecting through it. Further, directly accessing the state of
	objects through their names rather than by bind-to-edit does not disturb
	the bindings of the current context, which is useful for tools, middleware
	and other applications that are unaware of the outer state but it can also
	avoid cases of redundant state changes.
	
	There are several subtle differences between this extension and the older
	GL_EXT_direct_state_access extension. First, this extension only expands
	functionality that still exists in core profile OpenGL. Second, any function
	that only partially avoids bind-to-edit (for example, explicitly specifying
	a texture unit, bypassing the active texture selector but still indirecting
	through a texture binding) has been omitted. Finally, the original extension
	effectively allowed any function to create new objects whereas in unextended
	OpenGL, only binding functions created objects (bind-to-create), even if
	their names were obtained through one of the glGen* functions. This
	extension does not allow on-the-spot creation of objects. Rather than rely
	on bind-to-create (which would defeat the purpose of the extension), we add
	glCreate* functions that produce new names that represent state vectors
	initialized to their default values. Due to this last change, several
	functions no longer require their <target> parameters, and so where
	applicable, this parameter is absent from this extension.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/ARB/direct_state_access.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.ARB.direct_state_access import *
from OpenGL.raw.GL.ARB.direct_state_access import _EXTENSION_NAME

def glInitDirectStateAccessARB():
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
### END AUTOGENERATED SECTION