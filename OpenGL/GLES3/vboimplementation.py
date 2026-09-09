from OpenGL.arrays import vbo
from OpenGL.GLES3.VERSION import GLES3_3_0
# GL_OES_mapbuffer is an ES 2.0 extension and is bound in that namespace;
# ES 3.0 has no OES package of its own.  The entry points are the same ones,
# and ES 3.0 promoted the mapping calls into core, so this is the fallback for
# the names GLES3_3_0 does not carry rather than a second implementation.
from OpenGL.GLES2.OES import mapbuffer

class Implementation( vbo.Implementation ):
    """OpenGL-based implementation of VBO interfaces"""
    def __init__( self ):
        for name in self.EXPORTED_NAMES:
            for source in [ GLES3_3_0, mapbuffer ]:
                for possible in (name,name+'OES'):
                    try:
                        setattr( self, name, getattr( source, possible ))
                    except AttributeError as err:
                        pass 
                    else:
                        found = True
                assert found, name
        if GLES3_3_0.glBufferData:
            self.available = True
Implementation.register()
