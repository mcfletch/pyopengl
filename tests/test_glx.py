from OpenGL.GL import *
from OpenGL.GLX import *
from pygamegltest import pygametest

attributes = [
    GLX_BIND_TO_TEXTURE_RGBA_EXT, 1,
    GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
    GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
    GLX_DOUBLEBUFFER, 0,
    GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
    GL_NONE
]

@pygametest()
def main():
    d = glXGetCurrentDisplay()[0]
    elements = GLint(0)
    configs = glXChooseFBConfig(
        d, 
        0, 
        (GLint * len(attributes))( * attributes ), 
        elements
    )
    print '%s configs found'%( elements.value )
    for config in range( elements.value ):
        glxpix = glXCreatePixmap(d, configs[config], pixmap, None)
    
if __name__ == "__main__":
    main()
