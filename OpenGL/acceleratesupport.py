"""Common code for accelerated modules"""
import OpenGL,logging
needed_version = (3,0,1)
log = logging.getLogger( 'OpenGL.acceleratesupport' )
try:
    import OpenGL_accelerate
    if OpenGL.USE_ACCELERATE:
        if OpenGL_accelerate.__version_tuple__ <  needed_version:
            log.warn( """Incompatible version of OpenGL_accelerate found, need at least %s found %s""", needed_version, OpenGL_accelerate.__version_tuple__)
            raise ImportError( """Old version of OpenGL_accelerate""" )
        ACCELERATE_AVAILABLE = True
        log.info( """OpenGL_accelerate module loaded""" )
    else:
        raise ImportError( """Acceleration disabled""" )
except ImportError, err:
    log.info( """No OpenGL_accelerate module loaded: %s""", err )
    ACCELERATE_AVAILABLE = False