"""Convenience module providing common shader entry points

The point of this module is to allow client code to use
OpenGL 2.x style names to reference shader-related operations
even if the local hardware only supports ARB extension-based 
shader rendering.

There are also two utility methods compileProgram and compileShader
which make it easy to create demos which are shader-using.
"""
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
    'glGetProgramiv',
    'glGetShaderiv',
    'compileProgram',
    'compileShader',
    'GL_VALIDATE_STATUS',
    'GL_LINK_STATUS',
    # automatically added stuff here...
]

def _alt( base, name ):
    if hasattr( GL, base ):
        root = getattr( GL, base )
        if hasattr(root,'__call__'):
            globals()[base] = alternate( 
                getattr(GL,base),
                getattr(module,name)
            )
            __all__.append( base )
        else:
            globals()[base] = root
            __all__.append( base )
        return True 
    return False
_excludes = ['glGetProgramiv']
for module in shader_objects,fragment_shader,vertex_shader,vertex_program:
    for name in dir(module):
        found = None
        for suffix in ('ObjectARB','_ARB','ARB'):
            if name.endswith( suffix ):
                found = False 
                base = name[:-(len(suffix))]
                if base not in _excludes:
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

glGetShaderiv = alternate( GL.glGetShaderiv, shader_objects.glGetObjectParameterivARB )
glGetProgramiv = alternate( GL.glGetProgramiv, shader_objects.glGetObjectParameterivARB )

GL_VALIDATE_STATUS = GL.GL_VALIDATE_STATUS
GL_COMPILE_STATUS = GL.GL_COMPILE_STATUS
GL_LINK_STATUS = GL.GL_LINK_STATUS
GL_FALSE = GL.GL_FALSE

class ShaderProgram( int ):
    """Integer sub-class with context-manager operation"""
    def __enter__( self ):
        """Start use of the program"""
        glUseProgram( self )
    def __exit__( self, typ, val, tb ):
        """Stop use of the program"""
        glUseProgram( 0 )

def compileProgram(*shaders):
    """Create a new program, attach shaders and validate
    
    shaders -- arbitrary number of shaders to attach to the 
        generated program.
    
    This convenience function is *not* standard OpenGL,
    but it does wind up being fairly useful for demos 
    and the like.  You may wish to copy it to your code 
    base to guard against PyOpenGL changes.
    
    Usage:
    
        shader = compileProgram( 
            compileShader( source, GL_VERTEX_SHADER ),
            compileShader( source2, GL_FRAGMENT_SHADER ),
        )
        glUseProgram( shader )
    
    Note:
        If (and only if) validation of the linked program 
        *passes* then the passed-in shader objects will be 
        deleted from the GL.
    
    returns GLuint shader program reference
    raises RuntimeError when a link/validation failure occurs
    """
    program = glCreateProgram()
    for shader in shaders:
        glAttachShader(program, shader)
    glLinkProgram(program)
    # Validation has to occur *after* linking
    glValidateProgram( program )
    validation = glGetProgramiv( program, GL_VALIDATE_STATUS )
    if validation == GL_FALSE:
        raise RuntimeError(
            """Validation failure (%s): %s"""%(
            validation,
            glGetProgramInfoLog( program ),
        ))
    link_status = glGetProgramiv( program, GL_LINK_STATUS )
    if link_status == GL_FALSE:
        raise RuntimeError(
            """Link failure (%s): %s"""%(
            link_status,
            glGetProgramInfoLog( program ),
        ))
    for shader in shaders:
        glDeleteShader(shader)
    return ShaderProgram( program )
def compileShader( source, shaderType ):
    """Compile shader source of given type
    
    source -- GLSL source-code for the shader
    shaderType -- GLenum GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, etc,
    
    returns GLuint compiled shader reference
    raises RuntimeError when a compilation failure occurs
    """
    if isinstance( source, (str,unicode)):
        source = [ source ]
    shader = glCreateShader(shaderType)
    glShaderSource( shader, source )
    glCompileShader( shader )
    result = glGetShaderiv( shader, GL_COMPILE_STATUS )
    if not(result):
        # TODO: this will be wrong if the user has 
        # disabled traditional unpacking array support.
        raise RuntimeError(
            """Shader compile failure (%s): %s"""%(
                result,
                glGetShaderInfoLog( shader ),
            ),
            source,
            shaderType,
        )
    return shader
