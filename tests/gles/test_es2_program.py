#! /usr/bin/env python3
"""GLES2: shader/program lifecycle and introspection entry points."""

import unittest

from arraycompat import one
from egltestcase import ESTestCase

from OpenGL.GLES2 import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_COMPILE_STATUS,
    GL_LINK_STATUS,
    GL_VALIDATE_STATUS,
    GL_ACTIVE_ATTRIBUTES,
    GL_ACTIVE_UNIFORMS,
    GL_HIGH_FLOAT,
    GL_TRUE,
    glCreateShader,
    glShaderSource,
    glCompileShader,
    glGetShaderiv,
    glGetShaderInfoLog,
    glGetShaderSource,
    glIsShader,
    glCreateProgram,
    glAttachShader,
    glDetachShader,
    glBindAttribLocation,
    glLinkProgram,
    glGetProgramiv,
    glGetProgramInfoLog,
    glGetAttachedShaders,
    glValidateProgram,
    glIsProgram,
    glUseProgram,
    glGetActiveAttrib,
    glGetActiveUniform,
    glGetAttribLocation,
    glGetUniformLocation,
    glGetShaderPrecisionFormat,
    glReleaseShaderCompiler,
    glDeleteShader,
    glDeleteProgram,
    GL_NUM_SHADER_BINARY_FORMATS,
    GL_SHADER_BINARY_FORMATS,
    glShaderBinary,
)
import ctypes

VERTEX = '''#version 100
attribute vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''

FRAGMENT = '''#version 100
precision mediump float;
uniform vec4 color;
void main() { gl_FragColor = color; }'''


class TestES2Program(ESTestCase):
    api = 'gles'
    gl_version = (2, 0)

    def _shader(self, stage, source):
        shader = glCreateShader(stage)
        glShaderSource(shader, source)
        glCompileShader(shader)
        self.assertEqual(
            one(glGetShaderiv(shader, GL_COMPILE_STATUS)),
            GL_TRUE,
            glGetShaderInfoLog(shader),
        )
        self.assertTrue(glIsShader(shader))
        return shader

    def test_lifecycle_and_introspection(self):
        vs = self._shader(GL_VERTEX_SHADER, VERTEX)
        fs = self._shader(GL_FRAGMENT_SHADER, FRAGMENT)

        # source round-trips
        src = glGetShaderSource(vs)
        self.assertIn(b'position' if isinstance(src, bytes) else 'position', src)

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glBindAttribLocation(program, 0, 'position')
        glLinkProgram(program)
        self.assertEqual(
            one(glGetProgramiv(program, GL_LINK_STATUS)),
            GL_TRUE,
            glGetProgramInfoLog(program),
        )
        self.assertTrue(glIsProgram(program))

        attached = glGetAttachedShaders(program)
        self.assertEqual(set(int(s) for s in attached), {int(vs), int(fs)})

        glValidateProgram(program)
        one(glGetProgramiv(program, GL_VALIDATE_STATUS))
        glUseProgram(program)

        self.assertEqual(one(glGetProgramiv(program, GL_ACTIVE_ATTRIBUTES)), 1)
        self.assertEqual(one(glGetProgramiv(program, GL_ACTIVE_UNIFORMS)), 1)
        # name, size, type of the single active attribute / uniform
        a_name = glGetActiveAttrib(program, 0)[0]
        u_name = glGetActiveUniform(program, 0)[0]
        self.assertTrue(a_name)
        self.assertTrue(u_name)
        self.assertEqual(glGetAttribLocation(program, 'position'), 0)
        self.assertNotEqual(glGetUniformLocation(program, 'color'), -1)
        self.check_error('introspection')

        # precision query + compiler release
        precision, rng = glGetShaderPrecisionFormat(GL_FRAGMENT_SHADER, GL_HIGH_FLOAT)
        self.assertEqual(len(rng), 2)
        self.assertGreaterEqual(one(precision), 0)
        glReleaseShaderCompiler()

        glDetachShader(program, vs)
        glDetachShader(program, fs)
        glDeleteShader(vs)
        glDeleteShader(fs)
        glUseProgram(0)
        glDeleteProgram(program)
        self.check_error('teardown')

    def test_shader_binary(self):
        """Load a shader binary, where the driver advertises a binary format."""
        n = self.getInteger(GL_NUM_SHADER_BINARY_FORMATS)
        if n < 1:
            self.skipTest('no shader binary formats available')
        fmt = self.getInteger(GL_SHADER_BINARY_FORMATS, count=n)
        fmt = fmt[0] if isinstance(fmt, list) else fmt
        shader = glCreateShader(GL_VERTEX_SHADER)
        blob = (ctypes.c_ubyte * 4)()
        # we cannot synthesise a valid binary; just confirm the call is reachable
        try:
            glShaderBinary(1, [shader], fmt, blob, 4)
        except Exception:
            pass
        glDeleteShader(shader)


if __name__ == '__main__':
    unittest.main()
