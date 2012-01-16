#! /usr/bin/env python
"""Script to pull out OpenGL core definitions from the linux opengl header"""
import re
import get_gl_extensions
constant = re.compile( '^[#]define\W+(?P<name>[A-Z_0-9]+)\W+(?P<value>0x[a-fA-F0-9]+)$', re.M )
function = re.compile( '^GLAPI\W+(?P<return>[A-Z_0-9a-z *]+)\W+GLAPIENTRY\W+(?P<name>[a-zA-Z_0-9]+)(?P<signature>[(].*?[)])\W*[;]', re.DOTALL|re.M )

class CoreModule( get_gl_extensions.VersionModule ):
    _header = None
    dll = 'None'
    GLGET_CONSTANT = '_GLGET_CONSTANTS[ %(name)s ] = %(size)s'
    @property
    def RAW_MODULE_TEMPLATE( self ):
        assert not 'glget' in get_gl_extensions.WRAPPER_TEMPLATE
        return get_gl_extensions.WRAPPER_TEMPLATE + get_gl_extensions.INIT_TEMPLATE
    def read_header( self ):
        if not self._header:
            content = open( '/usr/include/GL/gl.h' ).read()
            start = content.index( ' * Constants' )
            stop = content.index( ' * OpenGL 1.2' )
            self._header = content[start:stop]
        return self._header

    def findFunctions( self ):
        declarations = self.read_header()
        functions = []
        for match in function.finditer(declarations):
            match_dict = match.groupdict()
            f = get_gl_extensions.Function( match_dict['return'], match_dict['name'], " ".join(match_dict['signature'].splitlines()) )
            if 'ptr' in f.argNames:
                f.argNames[f.argNames.index('ptr')] = 'pointer'
            functions.append( f )
        self.functions = functions

def core():
    # avoid import loops...
    get_gl_extensions.WRAPPER_TEMPLATE = get_gl_extensions.WRAPPER_TEMPLATE.replace( 
        'from OpenGL.GL import glget', '_GLGET_CONSTANTS = {}', 
    )
    assert not 'glget' in get_gl_extensions.WRAPPER_TEMPLATE
    class FakeHeader( object ):
        includeOverviews = False
        registry = {}
        glGetSizes = {}
        def loadGLGetSizes( self ):
            """Load manually-generated table of glGet* sizes"""
            table = self.glGetSizes
            try:
                lines = [
                    line.split('\t')
                    for line in open( 'glgetsizes.csv' ).read().splitlines()
                ]
            except IOError, err:
                pass 
            else:
                for line in lines:
                    if line and line[0]:
                        table[line[0].strip('"')] = [
                            v for v in [
                                v.strip('"') for v in line[1:]
                            ]
                            if v
                        ]
    f = FakeHeader()
    f.loadGLGetSizes()
    c = CoreModule( 'GL_VERSION_GL_1_1', [], f )
    c.segments = [c.read_header()]
    c.process()

if __name__ == "__main__":
    core()
