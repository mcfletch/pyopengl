"""Convenience module providing common shader entry points

The point of this module is to allow client code to use
OpenGL Core names to reference shader-related operations
even if the local hardware only supports ARB extension-based
shader rendering.

There are also two utility methods compileProgram and compileShader
which make it easy to create demos which are shader-using.
"""
import logging
log = logging.getLogger( __name__ )
from OpenGL import GL
from OpenGL.GL.ARB import (
    shader_objects, fragment_shader, vertex_shader, vertex_program,
    geometry_shader4, separate_shader_objects, get_program_binary,
)
from OpenGL.extensions import alternate
from OpenGL._bytes import bytes,unicode,as_8_bit

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
    'ShaderCompilationError', 
    'ShaderValidationError', 
    'ShaderLinkError',
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
for module in (
    shader_objects,fragment_shader,vertex_shader,vertex_program,
   geometry_shader4,
):
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
GL_TRUE = GL.GL_TRUE

#: Enums whose name carries the word SAMPLER but which are not uniform types:
#: a pname, an object-type token for debug labels, and a limit.  A set that
#: claims a pname is a uniform type is one nothing can be reasoned about.
_NOT_SAMPLER_TYPES = ( 'GL_SAMPLER', 'GL_SAMPLER_BINDING', 'GL_MAX_SAMPLES' )

#: Built on the first ask and kept: it describes the GL enums, not any program.
_SAMPLER_TYPES = None


def _sampler_types( ):
    """Every uniform type that is a sampler, as a set of enum values.

    Read off the constant names rather than listed, so a sampler target added
    by a later GL version counts from the day its enum arrives.
    """
    global _SAMPLER_TYPES
    if _SAMPLER_TYPES is None:
        excluded = frozenset(
            int( getattr( GL, name ) )
            for name in _NOT_SAMPLER_TYPES
            if getattr( GL, name, None ) is not None
        )
        _SAMPLER_TYPES = frozenset(
            int( value )
            for name, value in vars( GL ).items()
            if isinstance( value, int )
            and name.startswith( 'GL_' )
            and 'SAMPLER' in name.split( '_' )
            and int( value ) not in excluded
        )
    return _SAMPLER_TYPES


def _distinct_sampler_targets( program ):
    """How many differently-targeted samplers the linked program declares.

    Every sampler uniform reads texture image unit 0 until the program is
    given its units, so a program declaring two targets sits, the moment it
    links, in exactly the state ``glValidateProgram`` is required to reject:
    "active samplers with a different type refer to the same texture image
    unit".  A driver that answers strictly fails it; one that answers leniently
    does not; neither answer says anything about the program, only that its
    uniforms have not been set yet.  Ordinary shaders read a texture and a
    buffer, or a texture and a shadow map, so this is not a corner.

    Counts to two and stops, because two is the whole of what the caller asks:
    the alternative is a ``glGetActiveUniform`` round trip per uniform in the
    program, at every link.

    Returns 0 where the count cannot be had, which reads as "nothing to skip".
    """
    try:
        count = int( glGetProgramiv( program, GL.GL_ACTIVE_UNIFORMS ) )
    except Exception:  # a program object the driver will not describe
        return 0
    samplers = _sampler_types( )
    targets = set( )
    for index in range( count ):
        try:
            _name, _size, type_ = GL.glGetActiveUniform( program, index )
        except Exception:
            continue
        if int( type_ ) in samplers:
            targets.add( int( type_ ) )
            if len( targets ) > 1:
                break
    return len( targets )


class ShaderProgram( int ):
    """Integer sub-class with context-manager operation"""
    validated = False
    #: True where a validation the caller asked for was not performed because
    #: the answer would have been about the program's uniforms rather than
    #: about the program.  See :meth:`check_validate`.
    validation_deferred = False
    def __enter__( self ):
        """Start use of the program"""
        glUseProgram( self )
    def __exit__( self, typ, val, tb ):
        """Stop use of the program"""
        glUseProgram( 0 )
    
    def check_validate( self, when_meaningful=False ):
        """Check that the program validates

        Validation has to occur *after* linking/loading

        when_meaningful -- skip the check where the answer would be about the
            program's uniforms not having been set rather than about the
            program.  Used at link time, where that is always the case for a
            program with samplers of two targets; see
            :func:`_distinct_sampler_targets`.  An explicit call still checks
            unconditionally, because by then the caller has set its state and
            the answer means what it says.

        A skip is recorded on :attr:`validation_deferred` and logged, because
        the caller asked for a check and did not get one -- and the answer they
        did not get may have said something else about the program as well.

        raises ShaderValidationError on failures
        """
        if when_meaningful and _distinct_sampler_targets( self ) > 1:
            self.validation_deferred = True
            log.info(
                'Validation of program %s deferred: it declares samplers of '
                'two targets, which all read texture image unit 0 until the '
                'program is given its units. Call check_validate() once they '
                'are set.',
                int( self ),
            )
            return self
        glValidateProgram( self )
        validation = glGetProgramiv( self, GL_VALIDATE_STATUS )
        if validation == GL_FALSE:
            raise ShaderValidationError(
                """Validation failure (%r): %s"""%(
                validation,
                glGetProgramInfoLog( self ),
            ))
        self.validated = True
        self.validation_deferred = False
        return self

    def check_linked( self ):
        """Check link status for this program
        
        raises ShaderLinkError on failures
        """
        link_status = glGetProgramiv( self, GL_LINK_STATUS )
        if link_status == GL_FALSE:
            raise ShaderLinkError(
                """Link failure (%s): %s"""%(
                link_status,
                glGetProgramInfoLog( self ),
            ))
        return self

    def retrieve( self ):
        """Attempt to retrieve binary for this compiled shader

        Note that binaries for a program are *not* generally portable,
        they should be used solely for caching compiled programs for
        local use; i.e. to reduce compilation overhead.

        returns (format,binaryData) for the shader program
        """
        from OpenGL.raw.GL._types import GLint,GLenum
        from OpenGL.arrays import GLbyteArray
        size = GLint()
        glGetProgramiv( self, get_program_binary.GL_PROGRAM_BINARY_LENGTH, size )
        result = GLbyteArray.zeros( (size.value,))
        size2 = GLint()
        format = GLenum()
        binary, binaryFormat, length = get_program_binary.glGetProgramBinary(
            self, size.value, size2, format, result
        )
        # format was passed in and filled by the call
        return format.value, binary 
    def load( self, format, binary, validate=True ):
        """Attempt to load binary-format for a pre-compiled shader
        
        See notes in retrieve
        """
        get_program_binary.glProgramBinary( self, format, binary, len(binary))
        # Linked first: validating a program that did not link fails for that
        # reason, and reports it as a validation failure with the link log --
        # the one thing that says what went wrong -- left unread.
        self.check_linked()
        if validate:
            self.check_validate( when_meaningful=True )
        return self

def compileProgram(*shaders, **named):
    """Create a new program, attach shaders and validate

    shaders -- arbitrary number of shaders to attach to the
        generated program.
    separable (keyword only) -- set the separable flag to allow 
        for partial installation of shader into the pipeline (see 
        glUseProgramStages)
    retrievable (keyword only) -- set the retrievable flag to 
        allow retrieval of the program binary representation, (see 
        glProgramBinary, glGetProgramBinary)
    validate (keyword only) -- if False, suppress automatic 
        validation against current GL state. In advanced usage 
        the validation can produce spurious errors. Note: this 
        function is *not* really intended for advanced usage,
        if you're finding yourself specifying this flag you 
        likely should be using your own shader management code.

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

    returns ShaderProgram() (GLuint) program reference
    raises RuntimeError subclasses {
        ShaderCompilationError, ShaderValidationError, ShaderLinkError,
    } when a link/validation failure occurs
    """
    program = glCreateProgram()
    if named.get('separable'):
        glProgramParameteri( program, separate_shader_objects.GL_PROGRAM_SEPARABLE, GL_TRUE )
    if named.get('retrievable'):
        glProgramParameteri( program, get_program_binary.GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE )
    for shader in shaders:
        glAttachShader(program, shader)
    program = ShaderProgram( program )
    glLinkProgram(program)
    # Linked first: see ShaderProgram.load.
    program.check_linked()
    if named.get('validate', True):
        program.check_validate( when_meaningful=True )
    for shader in shaders:
        glDeleteShader(shader)
    return program
def compileShader( source, shaderType ):
    """Compile shader source of given type

    source -- GLSL source-code for the shader
    shaderType -- GLenum GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, etc,

    returns GLuint compiled shader reference
    raises RuntimeError when a compilation failure occurs
    """
    if isinstance( source, (bytes,unicode)):
        source = [ source ]
    source = [ as_8_bit(s) for s in source ]
    shader = glCreateShader(shaderType)
    glShaderSource( shader, source )
    glCompileShader( shader )
    result = glGetShaderiv( shader, GL_COMPILE_STATUS )
    if not(result):
        # TODO: this will be wrong if the user has
        # disabled traditional unpacking array support.
        raise ShaderCompilationError(
            """Shader compile failure (%s): %s"""%(
                result,
                glGetShaderInfoLog( shader ),
            ),
            source,
            shaderType,
        )
    return shader

class ShaderCompilationError(RuntimeError):
    """Raised when a shader compilation fails"""
class ShaderValidationError(RuntimeError):
    """Raised when a program fails to validate"""
class ShaderLinkError(RuntimeError):
    """Raised when a shader link fails"""