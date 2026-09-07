#! /usr/bin/env python3
"""Buffer / object extensions: storage, mapping, VAO, program binary,
sampler objects, framebuffer discard and external memory objects."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from arraycompat import copy_safe
from egltestcase import ESTestCase
from OpenGL.GLES3 import (
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_TEXTURE_MIN_FILTER,
    GL_NEAREST,
    GL_LINEAR,
    GL_RGBA8,
    GL_TEXTURE_2D,
    GL_TEXTURE_3D,
    GL_TEXTURE_2D_MULTISAMPLE,
    GL_TRUE,
    GL_MAP_WRITE_BIT,
    GL_MAP_FLUSH_EXPLICIT_BIT,
    GL_BUFFER_MAP_POINTER,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glGenTextures,
    glBindTexture,
)
from OpenGL.GLES2.EXT.buffer_storage import GL_DYNAMIC_STORAGE_BIT_EXT
from OpenGL.GLES2.OES.mapbuffer import GL_WRITE_ONLY_OES
from OpenGL.GLES2.EXT.memory_object import (
    GL_DEDICATED_MEMORY_OBJECT_EXT,
    GL_DEVICE_UUID_EXT,
    GL_DRIVER_UUID_EXT,
)
from OpenGL.GLES2.EXT import buffer_storage as ext_bufstore
from OpenGL.GLES2.OES import mapbuffer as oes_map
from OpenGL.GLES2.OES import vertex_array_object as oes_vao
from OpenGL.GLES2.OES import get_program_binary as oes_binary
from OpenGL.GLES2.MESA import sampler_objects as mesa_samplers
from OpenGL.GLES2.EXT import discard_framebuffer as ext_discard
from OpenGL.GLES2.EXT import map_buffer_range as ext_maprange
from OpenGL.GLES2.EXT import memory_object as ext_memory

VERTEX = '''#version 300 es
in vec4 p; void main() { gl_Position = p; }'''
FRAGMENT = '''#version 300 es
precision mediump float;
out vec4 c; void main() { c = vec4(1.0); }'''


class TestBufferExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def _array_buffer(self, nbytes=64):
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(
            GL_ARRAY_BUFFER, nbytes, np.zeros(nbytes // 4, 'f'), GL_STATIC_DRAW
        )
        return buf

    def test_mesa_sampler_objects(self):
        self.require_extension('GL_MESA_sampler_objects')
        with self.exercise(
            'GL_MESA_sampler_objects is advertised; a driver need not serve every entry point in it'
        ):
            ids = one(mesa_samplers.glGenSamplers(1))
            s = int(ids)
            mesa_samplers.glBindSampler(0, s)
            mesa_samplers.glSamplerParameteri(s, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            mesa_samplers.glSamplerParameterf(
                s, GL_TEXTURE_MIN_FILTER, float(GL_NEAREST)
            )
            mesa_samplers.glSamplerParameteriv(
                s, GL_TEXTURE_MIN_FILTER, [int(GL_NEAREST)]
            )
            mesa_samplers.glSamplerParameterfv(
                s, GL_TEXTURE_MIN_FILTER, [float(GL_NEAREST)]
            )
            mesa_samplers.glGetSamplerParameteriv(
                s, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'i')
            )
            mesa_samplers.glGetSamplerParameterfv(
                s, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'f')
            )
            self.assertTrue(mesa_samplers.glIsSampler(s))
            mesa_samplers.glDeleteSamplers(1, object_names(s))
            self.check_error('mesa sampler objects')

    def test_oes_vertex_array_object(self):
        self.require_extension('GL_OES_vertex_array_object')
        with self.exercise(
            'GL_OES_vertex_array_object is advertised; a driver need not serve every entry point in it'
        ):
            ids = np.zeros(1, 'u4')
            oes_vao.glGenVertexArraysOES(1, ids)
            vao = int(ids[0])
            oes_vao.glBindVertexArrayOES(vao)
            self.assertTrue(oes_vao.glIsVertexArrayOES(vao))
            oes_vao.glBindVertexArrayOES(0)
            oes_vao.glDeleteVertexArraysOES(1, object_names(vao))
            self.check_error('oes vao')

    def test_oes_get_program_binary(self):
        self.require_extension('GL_OES_get_program_binary')
        with self.exercise(
            'GL_OES_get_program_binary is advertised; a driver need not serve every entry point in it'
        ):
            from OpenGL.GLES3 import (
                glGetProgramiv,
                glCreateProgram,
                GL_PROGRAM_BINARY_LENGTH,
            )

            program = self.compile_program(VERTEX, FRAGMENT)
            length = one(glGetProgramiv(program, GL_PROGRAM_BINARY_LENGTH))
            if length < 1:
                self.skipTest('no retrievable binary')
            out_len = (ctypes.c_int * 1)()
            fmt = (ctypes.c_uint * 1)()
            binary = (ctypes.c_ubyte * length)()
            oes_binary.glGetProgramBinaryOES(program, length, out_len, fmt, binary)
            p2 = glCreateProgram()
            oes_binary.glProgramBinaryOES(p2, fmt[0], binary, out_len[0])
            self.check_error('oes program binary')

    def test_oes_mapbuffer(self):
        self.require_extension('GL_OES_mapbuffer')
        with self.exercise(
            'GL_OES_mapbuffer is advertised; a driver need not serve every entry point in it'
        ):
            self._array_buffer()
            oes_map.glMapBufferOES(GL_ARRAY_BUFFER, GL_WRITE_ONLY_OES)
            ptr = ctypes.c_void_p()
            oes_map.glGetBufferPointervOES(
                GL_ARRAY_BUFFER, GL_BUFFER_MAP_POINTER, ctypes.byref(ptr)
            )
            oes_map.glUnmapBufferOES(GL_ARRAY_BUFFER)
            self.check_error('oes mapbuffer')

    def test_ext_buffer_storage(self):
        self.require_extension('GL_EXT_buffer_storage')
        with self.exercise(
            'GL_EXT_buffer_storage is advertised; a driver need not serve every entry point in it'
        ):
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            ext_bufstore.glBufferStorageEXT(
                GL_ARRAY_BUFFER, 64, None, GL_DYNAMIC_STORAGE_BIT_EXT
            )
            self.check_error('ext buffer storage')

    def test_ext_map_buffer_range(self):
        self.require_extension('GL_EXT_map_buffer_range')
        with self.exercise(
            'GL_EXT_map_buffer_range is advertised; a driver need not serve every entry point in it'
        ):
            self._array_buffer()
            ext_maprange.glMapBufferRangeEXT(
                GL_ARRAY_BUFFER, 0, 32, GL_MAP_WRITE_BIT | GL_MAP_FLUSH_EXPLICIT_BIT
            )
            ext_maprange.glFlushMappedBufferRangeEXT(GL_ARRAY_BUFFER, 0, 32)
            from OpenGL.GLES3 import glUnmapBuffer

            glUnmapBuffer(GL_ARRAY_BUFFER)
            self.check_error('ext map buffer range')

    def test_ext_discard_framebuffer(self):
        self.require_extension('GL_EXT_discard_framebuffer')
        with self.exercise(
            'GL_EXT_discard_framebuffer is advertised; a driver need not serve every entry point in it'
        ):
            ext_discard.glDiscardFramebufferEXT(
                GL_FRAMEBUFFER, 1, copy_safe([GL_COLOR_ATTACHMENT0], 'I')
            )
            self.check_error('discard framebuffer')

    def test_ext_memory_object(self):
        self.require_extension('GL_EXT_memory_object')
        with self.exercise(
            'GL_EXT_memory_object is advertised; a driver need not serve every entry point in it'
        ):
            ids = np.zeros(1, 'u4')
            ext_memory.glCreateMemoryObjectsEXT(1, ids)
            mem = int(ids[0])
            self.assertIn(bool(ext_memory.glIsMemoryObjectEXT(mem)), (True, False))
            ext_memory.glMemoryObjectParameterivEXT(
                mem, GL_DEDICATED_MEMORY_OBJECT_EXT, np.array([1], 'i')
            )
            ext_memory.glGetMemoryObjectParameterivEXT(
                mem, GL_DEDICATED_MEMORY_OBJECT_EXT, np.zeros(1, 'i')
            )
            ext_memory.glGetUnsignedBytevEXT(GL_DEVICE_UUID_EXT, np.zeros(16, 'u1'))
            ext_memory.glGetUnsignedBytei_vEXT(
                GL_DRIVER_UUID_EXT, 0, np.zeros(16, 'u1')
            )
            ext_memory.glDeleteMemoryObjectsEXT(1, object_names(mem))
            self.check_error('memory object basics')
        with self.exercise(
            'storage-from-memory needs an imported external allocation we '
            'cannot make here, so these fail GL validation -- but they still '
            "drive the wrappers' argument marshalling, which is what we test"
        ):
            m2 = np.zeros(1, 'u4')
            ext_memory.glCreateMemoryObjectsEXT(1, m2)
            mm = int(m2[0])
            buf2 = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf2)
            ext_memory.glBufferStorageMemEXT(GL_ARRAY_BUFFER, 64, mm, 0)
            ext_memory.glNamedBufferStorageMemEXT(one(glGenBuffers(1)), 64, mm, 0)
            glBindTexture(GL_TEXTURE_2D, one(glGenTextures(1)))
            ext_memory.glTexStorageMem1DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4, mm, 0)
            ext_memory.glTexStorageMem2DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4, mm, 0)
            ext_memory.glTexStorageMem2DMultisampleEXT(
                GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 4, 4, GL_TRUE, mm, 0
            )
            glBindTexture(GL_TEXTURE_3D, one(glGenTextures(1)))
            ext_memory.glTexStorageMem3DEXT(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4, mm, 0)
            ext_memory.glTexStorageMem3DMultisampleEXT(
                GL_TEXTURE_3D, 4, GL_RGBA8, 4, 4, 4, GL_TRUE, mm, 0
            )
            ext_memory.glTextureStorageMem1DEXT(
                one(glGenTextures(1)), 1, GL_RGBA8, 4, mm, 0
            )
            ext_memory.glTextureStorageMem2DEXT(
                one(glGenTextures(1)), 1, GL_RGBA8, 4, 4, mm, 0
            )
            ext_memory.glTextureStorageMem2DMultisampleEXT(
                one(glGenTextures(1)), 4, GL_RGBA8, 4, 4, GL_TRUE, mm, 0
            )
            ext_memory.glTextureStorageMem3DEXT(
                one(glGenTextures(1)), 1, GL_RGBA8, 4, 4, 4, mm, 0
            )
            ext_memory.glTextureStorageMem3DMultisampleEXT(
                one(glGenTextures(1)), 4, GL_RGBA8, 4, 4, 4, GL_TRUE, mm, 0
            )


if __name__ == '__main__':
    unittest.main()
