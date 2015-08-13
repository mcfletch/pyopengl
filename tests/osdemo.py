#! /usr/bin/env python
from __future__ import print_function
import os
if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
from math import pi, sin, cos
import OpenGL
OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.GL.ARB.fragment_program import glGenProgramsARB
from OpenGL.GLU import *
from OpenGL.osmesa import *

def sphere(radius, slices, stacks):
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluSphere(q, radius, slices, stacks)
    gluDeleteQuadric(q)


def cone(base, height, slices, stacks):
    q = gluNewQuadric()
    gluQuadricDrawStyle(q, GLU_FILL)
    gluQuadricNormals(q, GLU_SMOOTH)
    gluCylinder(q, base, 0.0, height, slices, stacks)
    gluDeleteQuadric(q)


def torus(innerRadius, outerRadius, sides, rings):
    ringDelta = 2.0 * pi / rings
    sideDelta = 2.0 * pi / sides

    theta = 0.0
    cosTheta = 1.0
    sinTheta = 0.0
    for i in range(rings - 1, -1, -1):
        theta1 = theta + ringDelta
        cosTheta1 = cos(theta1)
        sinTheta1 = sin(theta1)
        glBegin(GL_QUAD_STRIP)
        phi = 0.0
        for j in range(sides, -1, -1):
            phi += sideDelta
            cosPhi = cos(phi)
            sinPhi = sin(phi)
            dist = outerRadius + innerRadius * cosPhi

            glNormal3f(cosTheta1 * cosPhi, -sinTheta1 * cosPhi, sinPhi)
            glVertex3f(cosTheta1 * dist, -sinTheta1 * dist, innerRadius * sinPhi)
            glNormal3f(cosTheta * cosPhi, -sinTheta * cosPhi, sinPhi)
            glVertex3f(cosTheta * dist, -sinTheta * dist,  innerRadius * sinPhi)
        glEnd()
        theta = theta1
        cosTheta = cosTheta1
        sinTheta = sinTheta1


def render_image():
    light_ambient = [0.0, 0.0, 0.0, 1.0]
    light_diffuse = [1.0, 1.0, 1.0, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]
    light_position = [1.0, 1.0, 1.0, 0.0]
    red_mat = [1.0, 0.2, 0.2, 1.0]
    green_mat = [0.2, 1.0, 0.2, 1.0]
    blue_mat = [0.2, 0.2, 1.0, 1.0]

    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-2.5, 2.5, -2.5, 2.5, -10.0, 10.0)
    glMatrixMode(GL_MODELVIEW)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glPushMatrix()
    glRotatef(20.0, 1.0, 0.0, 0.0)

    glPushMatrix()
    glTranslatef(-0.75, 0.5, 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, red_mat)
    torus(0.275, 0.85, 20, 20)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-0.75, -0.5, 0.0)
    glRotatef(270.0, 1.0, 0.0, 0.0)
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, green_mat)
    cone(1.0, 2.0, 16, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.75, 0.0, -1.0)
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, blue_mat)
    sphere(1.0, 20, 20)
    glPopMatrix()

    glPopMatrix()

    # This is very important!!!
    # Make sure buffered commands are finished!!!
    glFinish()


def write_ppm(buf, filename):
    f = open(filename, "w")
    if f:
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

if __name__ == '__main__':
    from OpenGL import arrays

    ctx = OSMesaCreateContext(OSMESA_RGBA, None)
    #ctx = OSMesaCreateContextExt(OSMESA_RGBA, 32, 0, 0, None)

    width, height = 400, 400
    buf = arrays.GLubyteArray.zeros((height, width, 4))
    assert(OSMesaMakeCurrent(ctx, buf, GL_UNSIGNED_BYTE, width, height))

    assert(OSMesaGetCurrentContext())
    
    program = glGenProgramsARB(1)
    assert(program)

    z = glGetIntegerv(GL_DEPTH_BITS)
    s = glGetIntegerv(GL_STENCIL_BITS)
    a = glGetIntegerv(GL_ACCUM_RED_BITS)
    print("Depth=%d Stencil=%d Accum=%d" % (z, s, a))

    print("Width=%d Height=%d" % (OSMesaGetIntegerv(OSMESA_WIDTH),
                                  OSMesaGetIntegerv(OSMESA_HEIGHT)))
    #OSMesaPixelStore(OSMESA_Y_UP, 0)

    render_image()

    write_ppm(buf, 'output.ppm')

    OSMesaDestroyContext(ctx)
