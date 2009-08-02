'''OpenGL extension VERSION.GL_1_4

The official definition of this extension is available here:
	http://oss.sgi.com/projects/ogl-sample/registry/VERSION/GL_1_4.txt

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_VERSION_GL_1_4'
GL_BLEND_DST_RGB = constant.Constant( 'GL_BLEND_DST_RGB', 0x80C8 )
GL_BLEND_SRC_RGB = constant.Constant( 'GL_BLEND_SRC_RGB', 0x80C9 )
GL_BLEND_DST_ALPHA = constant.Constant( 'GL_BLEND_DST_ALPHA', 0x80CA )
GL_BLEND_SRC_ALPHA = constant.Constant( 'GL_BLEND_SRC_ALPHA', 0x80CB )
GL_POINT_FADE_THRESHOLD_SIZE = constant.Constant( 'GL_POINT_FADE_THRESHOLD_SIZE', 0x8128 )
GL_DEPTH_COMPONENT16 = constant.Constant( 'GL_DEPTH_COMPONENT16', 0x81A5 )
GL_DEPTH_COMPONENT24 = constant.Constant( 'GL_DEPTH_COMPONENT24', 0x81A6 )
GL_DEPTH_COMPONENT32 = constant.Constant( 'GL_DEPTH_COMPONENT32', 0x81A7 )
GL_MIRRORED_REPEAT = constant.Constant( 'GL_MIRRORED_REPEAT', 0x8370 )
GL_MAX_TEXTURE_LOD_BIAS = constant.Constant( 'GL_MAX_TEXTURE_LOD_BIAS', 0x84FD )
GL_TEXTURE_LOD_BIAS = constant.Constant( 'GL_TEXTURE_LOD_BIAS', 0x8501 )
GL_INCR_WRAP = constant.Constant( 'GL_INCR_WRAP', 0x8507 )
GL_DECR_WRAP = constant.Constant( 'GL_DECR_WRAP', 0x8508 )
GL_TEXTURE_DEPTH_SIZE = constant.Constant( 'GL_TEXTURE_DEPTH_SIZE', 0x884A )
GL_TEXTURE_COMPARE_MODE = constant.Constant( 'GL_TEXTURE_COMPARE_MODE', 0x884C )
GL_TEXTURE_COMPARE_FUNC = constant.Constant( 'GL_TEXTURE_COMPARE_FUNC', 0x884D )
glBlendFuncSeparate = platform.createExtensionFunction( 
	'glBlendFuncSeparate', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, constants.GLenum, constants.GLenum, constants.GLenum,),
	doc = 'glBlendFuncSeparate( GLenum(sfactorRGB), GLenum(dfactorRGB), GLenum(sfactorAlpha), GLenum(dfactorAlpha) ) -> None',
	argNames = ('sfactorRGB', 'dfactorRGB', 'sfactorAlpha', 'dfactorAlpha',),
)

glMultiDrawArrays = platform.createExtensionFunction( 
	'glMultiDrawArrays', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, arrays.GLintArray, arrays.GLsizeiArray, constants.GLsizei,),
	doc = 'glMultiDrawArrays( GLenum(mode), GLintArray(first), GLsizeiArray(count), GLsizei(primcount) ) -> None',
	argNames = ('mode', 'first', 'count', 'primcount',),
)

glMultiDrawElements = platform.createExtensionFunction( 
	'glMultiDrawElements', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, arrays.GLsizeiArray, constants.GLenum, ctypes.POINTER(ctypes.c_void_p), constants.GLsizei,),
	doc = 'glMultiDrawElements( GLenum(mode), GLsizeiArray(count), GLenum(type), POINTER(ctypes.c_void_p)(indices), GLsizei(primcount) ) -> None',
	argNames = ('mode', 'count', 'type', 'indices', 'primcount',),
)

glPointParameterf = platform.createExtensionFunction( 
	'glPointParameterf', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, constants.GLfloat,),
	doc = 'glPointParameterf( GLenum(pname), GLfloat(param) ) -> None',
	argNames = ('pname', 'param',),
)

glPointParameterfv = platform.createExtensionFunction( 
	'glPointParameterfv', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, arrays.GLfloatArray,),
	doc = 'glPointParameterfv( GLenum(pname), GLfloatArray(params) ) -> None',
	argNames = ('pname', 'params',),
)

glPointParameteri = platform.createExtensionFunction( 
	'glPointParameteri', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, constants.GLint,),
	doc = 'glPointParameteri( GLenum(pname), GLint(param) ) -> None',
	argNames = ('pname', 'param',),
)

glPointParameteriv = platform.createExtensionFunction( 
	'glPointParameteriv', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, arrays.GLintArray,),
	doc = 'glPointParameteriv( GLenum(pname), GLintArray(params) ) -> None',
	argNames = ('pname', 'params',),
)
# import legacy entry points to allow checking for bool(entryPoint)
from OpenGL.raw.GL.VERSION.GL_1_4_DEPRECATED import *