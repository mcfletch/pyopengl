"""Extension module support methods

This module provides the tools required to check whether
an extension is available
"""
from OpenGL.latebind import LateBind
from OpenGL._bytes import bytes,as_8_bit
import OpenGL as root
import sys
import logging
log = logging.getLogger( 'OpenGL.extensions' )
VERSION_PREFIX = 'GL_VERSION_GL_'
CURRENT_GL_VERSION = None
AVAILABLE_GL_EXTENSIONS = []
AVAILABLE_GLU_EXTENSIONS = []

# version tuple -> list of implicitly included extensions...
VERSION_EXTENSIONS = [
    ((3,0), [
        'GL_ARB_vertex_array_object',
        'GL_ARB_texture_buffer_object',
        'GL_ARB_framebuffer_object',
        'GL_ARB_map_buffer_range',
    ]),
    ((3,1), [
        'GL_ARB_copy_buffer',
        'GL_ARB_uniform_buffer_object',
    ]),
    ((3,2), [
        'GL_ARB_draw_elements_base_vertex',
        'GL_ARB_provoking_vertex',
        'GL_ARB_sync',
        'GL_ARB_texture_multisample',
    ]),
    ((3,3), [
        'GL_ARB_texture_multisample',
        'GL_ARB_blend_func_extended',
        'GL_ARB_sampler_objects',
        'GL_ARB_explicit_attrib_location',
        'GL_ARB_occlusion_query2',
        'GL_ARB_shader_bit_encoding',
        'GL_ARB_texture_rgb10_a2ui',
        'GL_ARB_texture_swizzle',
        'GL_ARB_timer_query',
        'GL_ARB_vertex_type_2_10_10_10_rev',
    ]),
    ((4,0), [
        'GL_ARB_texture_query_lod',
        'GL_ARB_draw_indirect',
        'GL_ARB_gpu_shader5',
        'GL_ARB_gpu_shader_fp64',
        'GL_ARB_shader_subroutine',
        'GL_ARB_tessellation_shader',
        'GL_ARB_texture_buffer_object_rgb32',
        'GL_ARB_texture_cube_map_array',
        'GL_ARB_texture_gather',
        'GL_ARB_transform_feedback2',
        'GL_ARB_transform_feedback3',
    ]),
    ((4,1), [
        'GL_ARB_ES2_compatibility',
        'GL_ARB_get_program_binary',
        'GL_ARB_separate_shader_objects',
        'GL_ARB_shader_precision',
        'GL_ARB_vertex_attrib_64bit',
        'GL_ARB_viewport_array',
    ]),
]

def getGLVersion( ):
    """Retrieve 2-int declaration of major/minor GL version

    returns [int(major),int(minor)] or False if not loaded
    """
    global CURRENT_GL_VERSION
    if not CURRENT_GL_VERSION:
        from OpenGL.GL import glGetString, GL_VERSION
        new = glGetString( GL_VERSION )
        log.info( 'OpenGL Version: %s', new )
        if new:
            CURRENT_GL_VERSION = [
                int(x) for x in new.split(as_8_bit(' '),1)[0].split( as_8_bit('.') )
            ]
        else:
            return False # not yet loaded/supported
    return CURRENT_GL_VERSION


def hasGLExtension( specifier ):
    """Given a string specifier, check for extension being available"""
    global AVAILABLE_GL_EXTENSIONS
    specifier = specifier.replace(as_8_bit('.'),as_8_bit('_'))
    if specifier.startswith( VERSION_PREFIX ):
        specifier = [
            int(x)
            for x in specifier[ len(VERSION_PREFIX):].split(as_8_bit('_'))
        ]
        version = getGLVersion()
        if not version:
            return version
        return specifier <= version
    else:
        from OpenGL.GL import glGetString, GL_EXTENSIONS
        from OpenGL import error
        if not AVAILABLE_GL_EXTENSIONS:
            try:
                AVAILABLE_GL_EXTENSIONS[:] = glGetString( GL_EXTENSIONS ).split()
            except (AttributeError, error.GLError), err:
                # OpenGL 3.0 deprecates glGetString( GL_EXTENSIONS )
                from OpenGL.GL import GL_NUM_EXTENSIONS, glGetStringi, glGetIntegerv
                count = glGetIntegerv( GL_NUM_EXTENSIONS )
                for i in range( count ):
                    extension = glGetStringi( GL_EXTENSIONS, i )
                    AVAILABLE_GL_EXTENSIONS.append(
                        extension
                    )
            # Add included-by-reference extensions...
            version = getGLVersion()
            if not version:
                # should not be possible?
                return version 
            check = tuple( version[:2] )
            for (v,v_exts) in VERSION_EXTENSIONS:
                if v <= check:
                    for v_ext in v_exts:
                        if v_ext not in AVAILABLE_GL_EXTENSIONS:
                            AVAILABLE_GL_EXTENSIONS.append( v_ext )
                else:
                    break
        result = specifier in AVAILABLE_GL_EXTENSIONS
        log.info(
            'GL Extension %s %s',
            specifier,
            ['unavailable','available'][bool(result)]
        )
        return result

def hasGLUExtension( specifier ):
    """Given a string specifier, check for extension being available"""
    from OpenGL.GLU import gluGetString, GLU_EXTENSIONS
    if not AVAILABLE_GLU_EXTENSIONS:
        AVAILABLE_GLU_EXTENSIONS[:] = gluGetString( GLU_EXTENSIONS )
    return specifier.replace(as_8_bit('.'),as_8_bit('_')) in AVAILABLE_GLU_EXTENSIONS

class _Alternate( LateBind ):
    def __init__( self, name, *alternates ):
        """Initialize set of alternative implementations of the same function"""
        self.__name__ = name
        self._alternatives = alternates
        if root.MODULE_ANNOTATIONS:
            frame = sys._getframe().f_back
            if frame and frame.f_back and '__name__' in frame.f_back.f_globals:
                self.__module__ = frame.f_back.f_globals['__name__']
    def __nonzero__( self ):
        from OpenGL import error
        try:
            return bool( self.getFinalCall())
        except error.NullFunctionError, err:
            return False
    def finalise( self ):
        """Call, doing a late lookup and bind to find an implementation"""
        for alternate in self._alternatives:
            if alternate:
                log.info(
                    """Chose alternate: %s from %s""",
                    alternate.__name__,
                    ", ".join([x.__name__ for x in self._alternatives])
                )
                return alternate
        from OpenGL import error
        raise error.NullFunctionError(
            """Attempt to call an undefined alternate function (%s), check for bool(%s) before calling"""%(
                ', '.join([x.__name__ for x in self._alternatives]),
                self.__name__,
            )
        )
def alternate( name, *functions ):
    """Construct a callable that functions as the first implementation found of given set of alternatives

    if name is a function then its name will be used....
    """
    if not isinstance( name, (str,unicode)):
        functions = (name,)+functions
        name = name.__name__
    return type( name, (_Alternate,), {} )( name, *functions )
