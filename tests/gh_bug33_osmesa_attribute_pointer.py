from __future__ import print_function
import os
if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
import OpenGL
OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL import extensions
from OpenGL.GL.ARB.fragment_program import glGenProgramsARB
from OpenGL.GLU import *
from OpenGL.osmesa import *
from OpenGL.GL import shaders
from numpy import arange, array
import contextlib

def write_ppm(buf, filename):
    """Write traditional ASCII PPM file from buffer"""
    with open(filename, "w") as f:
        h, w, c = buf.shape
        print( "P3", file=f)
        print( "# ascii ppm file created by osmesa",file=f)
        print( "%i %i" % (w, h),file=f)
        print("255",file=f)
        for y in range(h - 1, -1, -1):
            for x in range(w):
                pixel = buf[y, x]
                l = " %3d %3d %3d" % (pixel[0], pixel[1], pixel[2])
                f.write(l)
            f.write("\n")

@contextlib.contextmanager
def osmesa_context(width=400, height=400, output='output.ppm'):
    """Do OSMesa rendering context setup and write to output if non-null"""
    from OpenGL import arrays
    ctx = OSMesaCreateContext(OSMESA_RGBA, None)
    buf = arrays.GLubyteArray.zeros((height, width, 4))
    assert(OSMesaMakeCurrent(ctx, buf, GL_UNSIGNED_BYTE, width, height))
    assert(OSMesaGetCurrentContext())
    yield (ctx, buf)
    if output:
        write_ppm(buf,output)
    OSMesaDestroyContext(ctx)

def setup():
    """Setup the rendering passes
    
    Taken from `OpenGLContext/tests/shader_4.py`
    """
    vertex = shaders.compileShader(
        """
        uniform float tween;
        attribute vec3 position;
        attribute vec3 tweened;
        attribute vec3 color;
        varying vec4 baseColor;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * mix(
                vec4( position,1.0),
                vec4( tweened,1.0),
                tween
            );
            baseColor = vec4(color,1.0);
        }""",
        GL_VERTEX_SHADER
    )
    fragment = shaders.compileShader(
        """
        varying vec4 baseColor;
        void main() {
            gl_FragColor = baseColor;
        }""",
        GL_FRAGMENT_SHADER
    )
    shader = shaders.compileProgram(vertex,fragment)
    vertices = vbo.VBO(
        array( [
            [  0, 1, 0, 1,3,0,  0,1,0 ],
            [ -1,-1, 0, -1,-1,0,  1,1,0 ],
            [  1,-1, 0, 1,-1,0, 0,1,1 ],
            
            [  2,-1, 0, 2,-1,0, 1,0,0 ],
            [  4,-1, 0, 4,-1,0, 0,1,0 ],
            [  4, 1, 0, 4,9,0, 0,0,1 ],
            [  2,-1, 0, 2,-1,0, 1,0,0 ],
            [  4, 1, 0, 1,3,0, 0,0,1 ],
            [  2, 1, 0, 1,-1,0, 0,1,1 ],
        ],'f')
    )
    position_location = glGetAttribLocation( 
        shader, 'position' 
    )
    tweened_location = glGetAttribLocation(
        shader, 'tweened',
    )
    color_location = glGetAttribLocation( 
        shader, 'color' 
    )
    tween_location = glGetUniformLocation(
        shader, 'tween',
    )
    return {
        'shader': shader,
        'position_location': position_location,
        'tweened_location': tweened_location,
        'color_location': color_location,
        'tween_location': tween_location,
        'vertices': vertices,
    }
def render(names, fraction=.5):
    glUseProgram(names['shader'])
    glUniform1f(names['tween_location'],  fraction)
    with names['vertices']:
        try:
            glEnableVertexAttribArray( names['position_location'] )
            glEnableVertexAttribArray( names['tweened_location'] )
            glEnableVertexAttribArray( names['color_location'] )
            stride = 9*4
            glVertexAttribPointer( 
                names['position_location'], 
                3, GL_FLOAT,False, stride, names['vertices'] 
            )
            glVertexAttribPointer( 
                names['tweened_location'], 
                3, GL_FLOAT,False, stride, names['vertices']+12
            )
            glVertexAttribPointer( 
                names['color_location'], 
                3, GL_FLOAT,False, stride, names['vertices']+24
            )
            glDrawArrays(GL_TRIANGLES, 0, 9)
        finally:
            glDisableVertexAttribArray( names['position_location'] )
            glDisableVertexAttribArray( names['tweened_location'] )
            glDisableVertexAttribArray( names['color_location'] )

def main():
    with osmesa_context(400,400) as context:
        print('Queried extensions:', sorted(extensions.GLQuerier.pullExtensions()))
        print('Queried version:', extensions.GLQuerier.pullVersion())
        names = setup()
        for fraction in arange(0,.5,.1):
            glClearColor(0.0,0.0,1.0,1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
            print("Rendering: %s"%(fraction,))
            render(names,fraction)
            glFinish()


if __name__ == '__main__':
    main()