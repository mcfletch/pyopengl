"""Convenience module providing common shader entry points with alternate implementations"""
import logging 
logging.basicConfig()
log = logging.getLogger( 'OpenGL.GL.shaders' )
from OpenGL import GL
from OpenGL.GL.ARB import shader_objects, fragment_shader, vertex_shader, vertex_program
from OpenGL.extensions import alternate

__all__ = [
	'glAttachShader',
	'glDeleteShader',
	'glGetProgramInfoLog',
	'glGetShaderInfoLog',
]

def _alt( base, name ):
	if hasattr( GL, base ):
		root = getattr( GL, base )
		if callable(root):
			globals()[base] = alternate( getattr(GL,base),getattr(module,name))
			__all__.append( base )
		else:
			globals()[base] = base
			__all__.append( base )
		return True 
	return False

for module in shader_objects,fragment_shader,vertex_shader,vertex_program:
	for name in dir(module):
		found = None
		for suffix in ('ObjectARB','_ARB','ARB'):
			if name.endswith( suffix ):
				found = False 
				base = name[:-(len(suffix))]
				if _alt( base, name ):
					found = True
					break 
		if found is False:
			log.debug( '''Found no alternate for: %s.%s''',
				module.__name__,name,
			)
	

glAttachShader = alternate( GL.glAttachShader,shader_objects.glAttachObjectARB )
glDetachShader = alternate( GL.glDetachShader,shader_objects.glDetachObjectARB )
glDeleteShader = alternate( GL.glDeleteShader,shader_objects.glDeleteObjectARB )
glGetAttachedShaders = alternate( GL.glGetAttachedShaders, shader_objects.glGetAttachedObjectsARB )

glGetProgramInfoLog = alternate( GL.glGetProgramInfoLog, shader_objects.glGetInfoLogARB )
glGetShaderInfoLog = alternate( GL.glGetShaderInfoLog, shader_objects.glGetInfoLogARB )
