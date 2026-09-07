#! /usr/bin/env python3
"""GLES2: framebuffer-object render-to-texture round-trip.

Renders a green triangle into an off-screen FBO backed by a texture, then binds
the default framebuffer and draws a full-screen quad sampling that texture,
verifying the result by pixel readback.  Exercises FBO completeness,
render-to-texture, and using the rendered texture as input -- the ES way to
"read back a texture" (glGetTexImage does not exist in ES).
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES2 import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_TRIANGLE_STRIP,
    GL_COLOR_BUFFER_BIT,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_NEAREST,
    GL_CLAMP_TO_EDGE,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_FRAMEBUFFER_COMPLETE,
    glViewport,
    glClear,
    glClearColor,
    glUseProgram,
    glGenTextures,
    glBindTexture,
    glActiveTexture,
    glTexParameteri,
    glTexImage2D,
    glGenFramebuffers,
    glBindFramebuffer,
    glFramebufferTexture2D,
    glCheckFramebufferStatus,
    glGetAttribLocation,
    glGetUniformLocation,
    glUniform1i,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
)
from OpenGL.arrays.vbo import VBO

SOLID_VERTEX = '''#version 100
attribute vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''

SOLID_FRAGMENT = '''#version 100
precision mediump float;
void main() { gl_FragColor = vec4( 0.0, 1.0, 0.0, 1.0 ); }'''

TEX_VERTEX = '''#version 100
attribute vec2 position;
attribute vec2 texcoord;
varying vec2 vtex;
void main() {
    vtex = texcoord;
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

TEX_FRAGMENT = '''#version 100
precision mediump float;
varying vec2 vtex;
uniform sampler2D tex;
void main() { gl_FragColor = texture2D( tex, vtex ); }'''

ORANGE = (255, 128, 0, 255)
GREEN = (0, 255, 0, 255)


class TestES2FBO(ESTestCase):
    api = 'gles'
    gl_version = (2, 0)

    def test_render_to_texture(self):
        fbo_size = 64
        # texture that backs the FBO colour attachment
        texture = one(glGenTextures(1))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            fbo_size,
            fbo_size,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )

        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0
        )
        self.assertEqual(
            glCheckFramebufferStatus(GL_FRAMEBUFFER), GL_FRAMEBUFFER_COMPLETE
        )

        # render a centred green triangle into the FBO over an orange clear
        glViewport(0, 0, fbo_size, fbo_size)
        glClearColor(1.0, 0.5, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        solid = self.compile_program(SOLID_VERTEX, SOLID_FRAGMENT)
        glUseProgram(solid)
        tri = VBO(np.array([(0.0, 0.8), (-0.8, -0.8), (0.8, -0.8)], dtype='f'))
        ploc = glGetAttribLocation(solid, 'position')
        with tri:
            glEnableVertexAttribArray(ploc)
            glVertexAttribPointer(ploc, 2, GL_FLOAT, GL_FALSE, 8, tri)
            glDrawArrays(GL_TRIANGLES, 0, 3)
        self.check_error('render to fbo')

        # back to the window: draw a full-screen quad sampling the FBO texture
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.25, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        textured = self.compile_program(TEX_VERTEX, TEX_FRAGMENT)
        glUseProgram(textured)
        glBindTexture(GL_TEXTURE_2D, texture)
        glUniform1i(glGetUniformLocation(textured, 'tex'), 0)
        quad = VBO(
            np.array(
                [(-1, -1, 0, 0), (1, -1, 1, 0), (-1, 1, 0, 1), (1, 1, 1, 1)],
                dtype='f',
            )
        )
        pos = glGetAttribLocation(textured, 'position')
        tc = glGetAttribLocation(textured, 'texcoord')
        with quad:
            glEnableVertexAttribArray(pos)
            glEnableVertexAttribArray(tc)
            glVertexAttribPointer(pos, 2, GL_FLOAT, GL_FALSE, 16, quad)
            glVertexAttribPointer(tc, 2, GL_FLOAT, GL_FALSE, 16, quad + 8)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        self.check_error('sample fbo texture')

        cx, cy = self.width // 2, self.height // 2
        self.assert_pixel(cx, cy, GREEN)  # centre: the triangle drawn into the FBO
        self.assert_pixel(4, 4, ORANGE)  # corner: the FBO clear colour


if __name__ == '__main__':
    unittest.main()
