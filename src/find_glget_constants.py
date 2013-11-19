#! /usr/bin/env python
"""Do a lot of hacking about to find glGet-able constants..."""
from OpenGL import constant, error
from OpenGL import GL
from OpenGL.raw.GL.VERSION.GL_1_0 import glGetIntegerv
from OpenGLContext import testingcontext
BaseContext = testingcontext.getInteractive()
from OpenGLContext import arrays
from OpenGL.GL import glget
import sys

class TestContext( BaseContext ):
    def OnInit( self ):
        """Do our testing here..."""
        weird_value = -701496917
        data = arrays.zeros( (256,),'i')
        for name in dir( GL ):
            value = getattr( GL, name )
            if isinstance( value, constant.Constant ):
                original_ord = glget.GL_GET_SIZES.get( value )
#                if value in glget.GL_GET_SIZES:
#                    print '# done', value
#                    continue
                data[:] = weird_value
                try:
                    glGetIntegerv(
                        value,
                        data 
                    )
                except error.GLError, err:
                    if err.err == 1280:
                        #print '# No: %s'%( value.name, )
                        pass
                    else:
                        print 'simple.%s: (1,), # TODO: Check size!'%( value.name, )
                else:
                    ordinality = 256 - arrays.sum( 
                        (data == weird_value)
                    )
                    if ordinality == 16:
                        ordinality = (4,4)
                    else:
                        ordinality = (ordinality,)
                    if original_ord != ordinality:
                        
                        print 'simple.%s: %s, # %s'%(value.name,ordinality,original_ord)
                    else:
                        pass
        sys.exit( 0)

if __name__ == "__main__":
    TestContext.ContextMainLoop()
    
