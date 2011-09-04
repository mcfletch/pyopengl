"""OSX specific extensions to GLUT"""
from OpenGL import platform

glutCheckLoop = platform.createBaseFunction( 
    'glutCheckLoop', dll=platform.GLUT, resultType=None, 
    argTypes=[],
    doc='glutCheckLoop(  ) -> None', 
    argNames=(),
)
