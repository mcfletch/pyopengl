#! /usr/bin/env python3
"""GL_EXT_direct_state_access -- pre-core selector-free state access.

Mesa implements the whole extension.  Every entry point is actually called so
the PyOpenGL wrapper's argument marshalling runs; calls that the driver rejects
for state reasons still exercise the wrapper and are tolerated by exercise()."""

import unittest
import ctypes
from arraycompat import nbytes, np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.EXT.direct_state_access import *  # noqa: F401,F403
from OpenGL.GL.NV import explicit_multisample

M = np.eye(4, dtype='f')
Md = np.eye(4, dtype='d')
PX = np.zeros((4, 4, 4), 'B')
PX1 = np.zeros((4, 4), 'B')
PX3 = np.zeros((2, 2, 2, 4), 'B')

FS = '''#version 420
uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
uniform double ud; uniform dvec2 ud2; uniform dvec3 ud3; uniform dvec4 ud4;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
uniform dmat2 dm2; uniform dmat3 dm3; uniform dmat4 dm4;
uniform dmat2x3 dm23; uniform dmat3x2 dm32; uniform dmat2x4 dm24;
uniform dmat4x2 dm42; uniform dmat3x4 dm34; uniform dmat4x3 dm43;
out vec4 c;
void main(){ c = vec4(uf+uv2.x+uv3.y+uv4.z + float(ui+ui2.x+ui3.y+ui4.z)
    + float(uu+uu2.x+uu3.y+uu4.z) + float(ud+ud2.x+ud3.y+ud4.z)
    + m2[0][0]+m3[0][0]+m4[0][0]+m23[0][0]+m32[0][0]+m24[0][0]+m42[0][0]+m34[0][0]+m43[0][0]
    + float(dm2[0][0]+dm3[0][0]+dm4[0][0]+dm23[0][0]+dm32[0][0]+dm24[0][0]+dm42[0][0]+dm34[0][0]+dm43[0][0])); }'''
VS = '#version 420\nin vec4 p; void main(){ gl_Position = p; }'


class TestEXTDSA(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def require(self):
        self.require_extension('GL_EXT_direct_state_access')

    def test_matrix(self):
        self.require()
        with self.allow_missing():
            glMatrixLoadIdentityEXT(GL_MODELVIEW)
            glMatrixLoadfEXT(GL_MODELVIEW, M)
            glMatrixLoaddEXT(GL_MODELVIEW, Md)
            glMatrixLoadTransposefEXT(GL_MODELVIEW, M)
            glMatrixLoadTransposedEXT(GL_MODELVIEW, Md)
            glMatrixMultfEXT(GL_MODELVIEW, M)
            glMatrixMultdEXT(GL_MODELVIEW, Md)
            glMatrixMultTransposefEXT(GL_MODELVIEW, M)
            glMatrixMultTransposedEXT(GL_MODELVIEW, Md)
            glMatrixFrustumEXT(GL_PROJECTION, -1, 1, -1, 1, 1, 10)
            glMatrixOrthoEXT(GL_PROJECTION, -1, 1, -1, 1, 1, 10)
            glMatrixRotatefEXT(GL_MODELVIEW, 30, 0, 0, 1)
            glMatrixRotatedEXT(GL_MODELVIEW, 30, 0, 0, 1)
            glMatrixScalefEXT(GL_MODELVIEW, 1, 1, 1)
            glMatrixScaledEXT(GL_MODELVIEW, 1, 1, 1)
            glMatrixTranslatefEXT(GL_MODELVIEW, 1, 0, 0)
            glMatrixTranslatedEXT(GL_MODELVIEW, 1, 0, 0)
            glMatrixPushEXT(GL_MODELVIEW)
            glMatrixPopEXT(GL_MODELVIEW)
        self.check_error('dsa matrix')

    def test_named_buffer(self):
        self.require()
        with self.allow_missing():
            buf = one(glGenBuffers(1))
            glNamedBufferDataEXT(buf, 64, np.zeros(16, 'f'), GL_DYNAMIC_DRAW)
            glNamedBufferStorageEXT(one(glGenBuffers(1)), 64, None, GL_MAP_READ_BIT)
            glNamedBufferSubDataEXT(buf, 0, 16, np.ones(4, 'f'))
            glGetNamedBufferParameterivEXT(buf, GL_BUFFER_SIZE, np.zeros(1, 'i'))
            glGetNamedBufferSubDataEXT(buf, 0, 16, np.zeros(16, 'B'))
            ptr = ctypes.c_void_p()
            glGetNamedBufferPointervEXT(buf, GL_BUFFER_MAP_POINTER, ctypes.byref(ptr))
            other = one(glGenBuffers(1))
            glNamedBufferDataEXT(other, 64, None, GL_DYNAMIC_DRAW)
            glNamedCopyBufferSubDataEXT(buf, other, 0, 0, 16)
            glClearNamedBufferDataEXT(buf, GL_R32F, GL_RED, GL_FLOAT, None)
            glClearNamedBufferSubDataEXT(buf, GL_R32F, 0, 16, GL_RED, GL_FLOAT, None)
            glMapNamedBufferRangeEXT(
                buf, 0, 16, GL_MAP_WRITE_BIT | GL_MAP_FLUSH_EXPLICIT_BIT
            )
            glFlushMappedNamedBufferRangeEXT(buf, 0, 16)
            glUnmapNamedBufferEXT(buf)
            glMapNamedBufferEXT(buf, GL_READ_ONLY)
            glUnmapNamedBufferEXT(buf)
        self.check_error('dsa named buffer')

    def test_texture(self):
        self.require()
        with self.allow_missing():
            tex = one(glGenTextures(1))
            glTextureImage2DEXT(
                tex, GL_TEXTURE_2D, 0, GL_RGBA8, 4, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, PX
            )
            glTextureSubImage2DEXT(
                tex, GL_TEXTURE_2D, 0, 0, 0, 4, 4, GL_RGBA, GL_UNSIGNED_BYTE, PX
            )
            glTextureParameteriEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST
            )
            glTextureParameterfEXT(tex, GL_TEXTURE_2D, GL_TEXTURE_MAX_LOD, 0.0)
            glTextureParameterivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, np.array([GL_NEAREST], 'i')
            )
            glTextureParameterfvEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'f')
            )
            glTextureParameterIivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.array([GL_RED] * 4, 'i')
            )
            glTextureParameterIuivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.array([GL_RED] * 4, 'I')
            )
            glGenerateTextureMipmapEXT(tex, GL_TEXTURE_2D)
            glGetTextureParameterivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'i')
            )
            glGetTextureParameterfvEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_MAX_LOD, np.zeros(1, 'f')
            )
            glGetTextureParameterIivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.zeros(4, 'i')
            )
            glGetTextureParameterIuivEXT(
                tex, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.zeros(4, 'I')
            )
            glGetTextureLevelParameterivEXT(
                tex, GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'i')
            )
            glGetTextureLevelParameterfvEXT(
                tex, GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'f')
            )
            glGetTextureImageEXT(
                tex,
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                np.zeros((4, 4, 4), 'B'),
            )
            st = one(glGenTextures(1))
            glTextureStorage2DEXT(st, GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            glBindMultiTextureEXT(GL_TEXTURE0, GL_TEXTURE_2D, tex)
            ct = one(glGenTextures(1))
            glCopyTextureImage2DEXT(ct, GL_TEXTURE_2D, 0, GL_RGBA8, 0, 0, 4, 4, 0)
            glCopyTextureSubImage2DEXT(ct, GL_TEXTURE_2D, 0, 0, 0, 0, 0, 4, 4)
            tb = one(glGenTextures(1))
            tbb = one(glGenBuffers(1))
            glNamedBufferDataEXT(tbb, 64, None, GL_STATIC_DRAW)
            glTextureBufferEXT(tb, GL_TEXTURE_BUFFER, GL_R32F, tbb)
        self.check_error('dsa texture')

    def test_texture_dim_variants(self):
        self.require()
        with self.allow_missing():
            t1 = one(glGenTextures(1))
            glTextureImage1DEXT(
                t1, GL_TEXTURE_1D, 0, GL_RGBA8, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, PX1
            )
            glTextureSubImage1DEXT(
                t1, GL_TEXTURE_1D, 0, 0, 4, GL_RGBA, GL_UNSIGNED_BYTE, PX1
            )
            ts1 = one(glGenTextures(1))
            glTextureStorage1DEXT(ts1, GL_TEXTURE_1D, 1, GL_RGBA8, 4)
            t3 = one(glGenTextures(1))
            glTextureImage3DEXT(
                t3,
                GL_TEXTURE_3D,
                0,
                GL_RGBA8,
                2,
                2,
                2,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                PX3,
            )
            glTextureSubImage3DEXT(
                t3, GL_TEXTURE_3D, 0, 0, 0, 0, 2, 2, 2, GL_RGBA, GL_UNSIGNED_BYTE, PX3
            )
            ts3 = one(glGenTextures(1))
            glTextureStorage3DEXT(ts3, GL_TEXTURE_3D, 1, GL_RGBA8, 2, 2, 2)
            ct1 = one(glGenTextures(1))
            glTextureImage1DEXT(
                ct1, GL_TEXTURE_1D, 0, GL_RGBA8, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, PX1
            )
            # Intel's Windows driver serves this one only when some texture is
            # already bound to GL_TEXTURE_1D on the active unit, which is the
            # binding DSA exists to do without; binding one first makes the
            # same call succeed. Exercise the entry point either way.
            with self.tolerate_glerror(GL_INVALID_VALUE):
                glCopyTextureImage1DEXT(ct1, GL_TEXTURE_1D, 0, GL_RGBA8, 0, 0, 4, 0)
            glCopyTextureSubImage1DEXT(ct1, GL_TEXTURE_1D, 0, 0, 0, 0, 4)
            glCopyTextureSubImage3DEXT(ts3, GL_TEXTURE_3D, 0, 0, 0, 0, 0, 0, 2, 2)
            tbr = one(glGenTextures(1))
            bb = one(glGenBuffers(1))
            glNamedBufferDataEXT(bb, 64, None, GL_STATIC_DRAW)
            glTextureBufferRangeEXT(tbr, GL_TEXTURE_BUFFER, GL_R32F, bb, 0, 64)
        self.check_error('dsa texture dims')
        with self.exercise(
            'the EXT_DSA multisample-storage, texture-from-renderbuffer and '
            'sparse page-commitment paths are not implemented by this driver; '
            'the calls still drive the wrappers'
        ):
            tms = one(glGenTextures(1))
            glTextureStorage2DMultisampleEXT(
                tms, GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 4, 4, GL_TRUE
            )
            tms3 = one(glGenTextures(1))
            glTextureStorage3DMultisampleEXT(
                tms3, GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 4, 4, 2, GL_TRUE
            )
            trb = one(glGenTextures(1))
            rb = one(glGenRenderbuffers(1))
            glNamedRenderbufferStorageEXT(rb, GL_RGBA8, 4, 4)
            glTextureRenderbufferEXT(trb, explicit_multisample.GL_TEXTURE_RENDERBUFFER_NV, rb)
            tsp = one(glGenTextures(1))
            glTextureStorage2DEXT(tsp, GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            glTexturePageCommitmentEXT(tsp, 0, 0, 0, 0, 4, 4, 1, GL_TRUE)

    def test_compressed_texture(self):
        self.require()
        fmt = GL_COMPRESSED_RGB8_ETC2
        cdata = np.zeros(8, 'B')  # one ETC2 4x4 RGB block
        with self.allow_missing():
            t2 = one(glGenTextures(1))
            glCompressedTextureImage2DEXT(
                t2, GL_TEXTURE_2D, 0, fmt, 4, 4, 0, nbytes(cdata), cdata
            )
            glCompressedTextureSubImage2DEXT(
                t2, GL_TEXTURE_2D, 0, 0, 0, 4, 4, fmt, nbytes(cdata), cdata
            )
            glGetCompressedTextureImageEXT(t2, GL_TEXTURE_2D, 0, np.zeros(8, 'B'))
        self.check_error('dsa compressed texture')
        # compressed 1D/3D targets are not valid for ETC2; the calls still drive
        # the wrappers, and exercise() tolerates the resulting GLError
        with self.exercise(
            'compressed 1D/3D targets are not valid for ETC2; the calls still '
            'drive the wrappers'
        ):
            t1 = one(glGenTextures(1))
            glCompressedTextureImage1DEXT(
                t1, GL_TEXTURE_1D, 0, fmt, 4, 0, nbytes(cdata), cdata
            )
            glCompressedTextureSubImage1DEXT(
                t1, GL_TEXTURE_1D, 0, 0, 4, fmt, nbytes(cdata), cdata
            )
            t3 = one(glGenTextures(1))
            glCompressedTextureImage3DEXT(
                t3, GL_TEXTURE_3D, 0, fmt, 4, 4, 1, 0, nbytes(cdata), cdata
            )
            glCompressedTextureSubImage3DEXT(
                t3, GL_TEXTURE_3D, 0, 0, 0, 0, 4, 4, 1, fmt, nbytes(cdata), cdata
            )

    def test_multitex(self):
        self.require()
        with self.allow_missing():
            glMultiTexImage2DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                0,
                GL_RGBA8,
                4,
                4,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                PX,
            )
            glMultiTexSubImage2DEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, 0, 0, 0, 4, 4, GL_RGBA, GL_UNSIGNED_BYTE, PX
            )
            glMultiTexParameteriEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST
            )
            glMultiTexParameterfEXT(GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_MAX_LOD, 0.0)
            glMultiTexParameterivEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                GL_TEXTURE_MIN_FILTER,
                np.array([GL_NEAREST], 'i'),
            )
            glMultiTexParameterfvEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'f')
            )
            glMultiTexParameterIivEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                GL_TEXTURE_SWIZZLE_RGBA,
                np.array([GL_RED] * 4, 'i'),
            )
            glMultiTexParameterIuivEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                GL_TEXTURE_SWIZZLE_RGBA,
                np.array([GL_RED] * 4, 'I'),
            )
            glMultiTexEnvfEXT(
                GL_TEXTURE0, GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE
            )
            glMultiTexEnviEXT(
                GL_TEXTURE0, GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE
            )
            glMultiTexEnvfvEXT(
                GL_TEXTURE0, GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, np.zeros(4, 'f')
            )
            glMultiTexEnvivEXT(
                GL_TEXTURE0,
                GL_TEXTURE_ENV,
                GL_TEXTURE_ENV_MODE,
                np.array([GL_MODULATE], 'i'),
            )
            glMultiTexGeniEXT(GL_TEXTURE0, GL_S, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
            glMultiTexGenfEXT(GL_TEXTURE0, GL_S, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
            glMultiTexGendEXT(GL_TEXTURE0, GL_S, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
            glMultiTexGenivEXT(
                GL_TEXTURE0,
                GL_S,
                GL_TEXTURE_GEN_MODE,
                np.array([GL_OBJECT_LINEAR], 'i'),
            )
            glMultiTexGenfvEXT(GL_TEXTURE0, GL_S, GL_OBJECT_PLANE, np.zeros(4, 'f'))
            glMultiTexGendvEXT(GL_TEXTURE0, GL_S, GL_OBJECT_PLANE, np.zeros(4, 'd'))
            glGetMultiTexParameterivEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'i')
            )
            glGetMultiTexParameterfvEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_MAX_LOD, np.zeros(1, 'f')
            )
            glGetMultiTexParameterIivEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.zeros(4, 'i')
            )
            glGetMultiTexParameterIuivEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, np.zeros(4, 'I')
            )
            glGetMultiTexLevelParameterivEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'i')
            )
            glGetMultiTexLevelParameterfvEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'f')
            )
            glGetMultiTexEnvivEXT(
                GL_TEXTURE0, GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, np.zeros(1, 'i')
            )
            glGetMultiTexEnvfvEXT(
                GL_TEXTURE0, GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, np.zeros(4, 'f')
            )
            glGetMultiTexGenivEXT(
                GL_TEXTURE0, GL_S, GL_TEXTURE_GEN_MODE, np.zeros(1, 'i')
            )
            glGetMultiTexGenfvEXT(GL_TEXTURE0, GL_S, GL_OBJECT_PLANE, np.zeros(4, 'f'))
            glGetMultiTexGendvEXT(GL_TEXTURE0, GL_S, GL_OBJECT_PLANE, np.zeros(4, 'd'))
            glGetMultiTexImageEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                np.zeros((4, 4, 4), 'B'),
            )
            glGenerateMultiTexMipmapEXT(GL_TEXTURE0, GL_TEXTURE_2D)
        self.check_error('dsa multitex')

    def test_multitex_variants(self):
        self.require()
        cdata = np.zeros(8, 'B')
        with self.allow_missing():
            glMultiTexImage1DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_1D,
                0,
                GL_RGBA8,
                4,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                PX1,
            )
            glMultiTexSubImage1DEXT(
                GL_TEXTURE0, GL_TEXTURE_1D, 0, 0, 4, GL_RGBA, GL_UNSIGNED_BYTE, PX1
            )
            glMultiTexImage3DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_3D,
                0,
                GL_RGBA8,
                2,
                2,
                2,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                PX3,
            )
            glMultiTexSubImage3DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_3D,
                0,
                0,
                0,
                0,
                2,
                2,
                2,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                PX3,
            )
            glCopyMultiTexImage1DEXT(
                GL_TEXTURE0, GL_TEXTURE_1D, 0, GL_RGBA8, 0, 0, 4, 0
            )
            glCopyMultiTexImage2DEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, 0, GL_RGBA8, 0, 0, 4, 4, 0
            )
            glCopyMultiTexSubImage1DEXT(GL_TEXTURE0, GL_TEXTURE_1D, 0, 0, 0, 0, 4)
            glCopyMultiTexSubImage2DEXT(GL_TEXTURE0, GL_TEXTURE_2D, 0, 0, 0, 0, 0, 4, 4)
            glCopyMultiTexSubImage3DEXT(
                GL_TEXTURE0, GL_TEXTURE_3D, 0, 0, 0, 0, 0, 0, 2, 2
            )
            cbuf = one(glGenBuffers(1))
            glNamedBufferDataEXT(cbuf, 32, np.zeros(8, 'f'), GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, cbuf)
            glMultiTexCoordPointerEXT(GL_TEXTURE0, 2, GL_FLOAT, 0, None)
        self.check_error('dsa multitex variants')
        # generic GL_COMPRESSED_RGBA is not a valid compressed upload format and
        # multitex-renderbuffer is unimplemented here; calls drive the wrappers
        with self.exercise(
            'generic GL_COMPRESSED_RGBA is not a valid compressed upload format '
            'and multitex-renderbuffer is unimplemented here; calls drive the '
            'wrappers'
        ):
            glCompressedMultiTexImage1DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_1D,
                0,
                GL_COMPRESSED_RGBA,
                4,
                0,
                nbytes(cdata),
                cdata,
            )
            glCompressedMultiTexImage2DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                0,
                GL_COMPRESSED_RGBA,
                4,
                4,
                0,
                nbytes(cdata),
                cdata,
            )
            glCompressedMultiTexImage3DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_3D,
                0,
                GL_COMPRESSED_RGBA,
                4,
                4,
                1,
                0,
                nbytes(cdata),
                cdata,
            )
            glCompressedMultiTexSubImage1DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_1D,
                0,
                0,
                4,
                GL_COMPRESSED_RGBA,
                nbytes(cdata),
                cdata,
            )
            glCompressedMultiTexSubImage2DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_2D,
                0,
                0,
                0,
                4,
                4,
                GL_COMPRESSED_RGBA,
                nbytes(cdata),
                cdata,
            )
            glCompressedMultiTexSubImage3DEXT(
                GL_TEXTURE0,
                GL_TEXTURE_3D,
                0,
                0,
                0,
                0,
                4,
                4,
                1,
                GL_COMPRESSED_RGBA,
                nbytes(cdata),
                cdata,
            )
            glGetCompressedMultiTexImageEXT(
                GL_TEXTURE0, GL_TEXTURE_2D, 0, np.zeros(8, 'B')
            )
            mbuf = one(glGenBuffers(1))
            glNamedBufferDataEXT(mbuf, 64, None, GL_STATIC_DRAW)
            glMultiTexBufferEXT(GL_TEXTURE0, GL_TEXTURE_BUFFER, GL_R32F, mbuf)
            mrb = one(glGenRenderbuffers(1))
            glNamedRenderbufferStorageEXT(mrb, GL_RGBA8, 4, 4)
            glMultiTexRenderbufferEXT(GL_TEXTURE0, explicit_multisample.GL_TEXTURE_RENDERBUFFER_NV, mrb)

    def test_named_framebuffer(self):
        self.require()
        with self.allow_missing():
            fbo = one(glGenFramebuffers(1))
            rbo = one(glGenRenderbuffers(1))
            glNamedRenderbufferStorageEXT(rbo, GL_RGBA8, 16, 16)
            glNamedRenderbufferStorageMultisampleEXT(
                one(glGenRenderbuffers(1)), 4, GL_RGBA8, 16, 16
            )
            glNamedRenderbufferStorageMultisampleCoverageEXT(
                one(glGenRenderbuffers(1)), 4, 4, GL_RGBA8, 16, 16
            )
            glGetNamedRenderbufferParameterivEXT(
                rbo, GL_RENDERBUFFER_WIDTH, np.zeros(1, 'i')
            )
            glNamedFramebufferRenderbufferEXT(
                fbo, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rbo
            )
            tex = one(glGenTextures(1))
            glTextureImage2DEXT(
                tex,
                GL_TEXTURE_2D,
                0,
                GL_RGBA8,
                16,
                16,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                None,
            )
            glNamedFramebufferTexture2DEXT(
                fbo, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0
            )
            glNamedFramebufferTextureEXT(fbo, GL_COLOR_ATTACHMENT0, tex, 0)
            t1 = one(glGenTextures(1))
            glTextureImage1DEXT(
                t1, GL_TEXTURE_1D, 0, GL_RGBA8, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glNamedFramebufferTexture1DEXT(
                one(glGenFramebuffers(1)), GL_COLOR_ATTACHMENT0, GL_TEXTURE_1D, t1, 0
            )
            t3 = one(glGenTextures(1))
            glTextureImage3DEXT(
                t3,
                GL_TEXTURE_3D,
                0,
                GL_RGBA8,
                4,
                4,
                4,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                None,
            )
            glNamedFramebufferTexture3DEXT(
                one(glGenFramebuffers(1)), GL_COLOR_ATTACHMENT0, GL_TEXTURE_3D, t3, 0, 0
            )
            arr = one(glGenTextures(1))
            glTextureImage3DEXT(
                arr,
                GL_TEXTURE_2D_ARRAY,
                0,
                GL_RGBA8,
                4,
                4,
                2,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                None,
            )
            glNamedFramebufferTextureLayerEXT(
                one(glGenFramebuffers(1)), GL_COLOR_ATTACHMENT0, arr, 0, 0
            )
            # A cube-map face attach needs an actual cube-map texture; attaching
            # a 2D texture here is invalid and NVIDIA (correctly) rejects it.
            cube = one(glGenTextures(1))
            for face in range(6):
                glTextureImage2DEXT(
                    cube, GL_TEXTURE_CUBE_MAP_POSITIVE_X + face, 0, GL_RGBA8,
                    4, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, None,
                )
            glNamedFramebufferTextureFaceEXT(
                one(glGenFramebuffers(1)),
                GL_COLOR_ATTACHMENT0,
                cube,
                0,
                GL_TEXTURE_CUBE_MAP_POSITIVE_X,
            )
            glNamedFramebufferParameteriEXT(fbo, GL_FRAMEBUFFER_DEFAULT_WIDTH, 16)
            glGetNamedFramebufferParameterivEXT(
                fbo, GL_FRAMEBUFFER_DEFAULT_WIDTH, np.zeros(1, 'i')
            )
            glGetNamedFramebufferAttachmentParameterivEXT(
                fbo,
                GL_COLOR_ATTACHMENT0,
                GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE,
                np.zeros(1, 'i'),
            )
            glCheckNamedFramebufferStatusEXT(fbo, GL_FRAMEBUFFER)
            glFramebufferDrawBufferEXT(fbo, GL_COLOR_ATTACHMENT0)
            glFramebufferDrawBuffersEXT(fbo, 1, np.array([GL_COLOR_ATTACHMENT0], 'I'))
            glFramebufferReadBufferEXT(fbo, GL_COLOR_ATTACHMENT0)
            glGetFramebufferParameterivEXT(fbo, GL_DRAW_BUFFER0, np.zeros(1, 'i'))
        self.check_error('dsa named framebuffer')

    def test_vertex_array(self):
        self.require()
        with self.allow_missing():
            vao = one(glGenVertexArrays(1))
            buf = one(glGenBuffers(1))
            glNamedBufferDataEXT(buf, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
            glEnableVertexArrayEXT(vao, GL_VERTEX_ARRAY)
            glDisableVertexArrayEXT(vao, GL_VERTEX_ARRAY)
            glEnableVertexArrayAttribEXT(vao, 0)
            glDisableVertexArrayAttribEXT(vao, 0)
            glVertexArrayVertexAttribFormatEXT(vao, 0, 4, GL_FLOAT, GL_FALSE, 0)
            glVertexArrayVertexAttribIFormatEXT(vao, 1, 4, GL_INT, 0)
            glVertexArrayVertexAttribLFormatEXT(vao, 2, 4, GL_DOUBLE, 0)
            glVertexArrayVertexAttribBindingEXT(vao, 0, 0)
            glVertexArrayVertexBindingDivisorEXT(vao, 0, 0)
            glVertexArrayVertexAttribDivisorEXT(vao, 0, 0)
            glVertexArrayBindVertexBufferEXT(vao, 0, buf, 0, 16)
            glVertexArrayVertexAttribOffsetEXT(
                vao, buf, 0, 4, GL_FLOAT, GL_FALSE, 16, 0
            )
            glVertexArrayVertexAttribIOffsetEXT(vao, buf, 1, 4, GL_INT, 16, 0)
            glVertexArrayVertexAttribLOffsetEXT(vao, buf, 2, 4, GL_DOUBLE, 32, 0)
        self.check_error('dsa vertex array')
        # the EXT_DSA vertex-array getters only accept the legacy client-array
        # enums this driver does not map here; calls still drive the wrappers
        with self.exercise(
            'the EXT_DSA vertex-array getters only accept the legacy client- '
            'array enums this driver does not map here; calls still drive the '
            'wrappers'
        ):
            glGetVertexArrayIntegervEXT(
                vao, GL_ELEMENT_ARRAY_BUFFER_BINDING, np.zeros(1, 'i')
            )
            glGetVertexArrayIntegeri_vEXT(
                vao, 0, GL_VERTEX_ATTRIB_ARRAY_ENABLED, np.zeros(1, 'i')
            )
            ptr = ctypes.c_void_p()
            glGetVertexArrayPointervEXT(vao, GL_VERTEX_ARRAY_POINTER, ctypes.byref(ptr))
            glGetVertexArrayPointeri_vEXT(
                vao, 0, GL_VERTEX_ATTRIB_ARRAY_POINTER, ctypes.byref(ptr)
            )

    def test_vertex_array_legacy_offsets(self):
        self.require()
        with self.allow_missing():
            vao = one(glGenVertexArrays(1))
            buf = one(glGenBuffers(1))
            glNamedBufferDataEXT(buf, 256, np.zeros(64, 'f'), GL_STATIC_DRAW)
            glVertexArrayVertexOffsetEXT(vao, buf, 3, GL_FLOAT, 0, 0)
            glVertexArrayColorOffsetEXT(vao, buf, 4, GL_FLOAT, 0, 0)
            glVertexArrayEdgeFlagOffsetEXT(vao, buf, 0, 0)
            glVertexArrayIndexOffsetEXT(vao, buf, GL_FLOAT, 0, 0)
            glVertexArrayNormalOffsetEXT(vao, buf, GL_FLOAT, 0, 0)
            glVertexArrayTexCoordOffsetEXT(vao, buf, 2, GL_FLOAT, 0, 0)
            glVertexArrayMultiTexCoordOffsetEXT(
                vao, buf, GL_TEXTURE0, 2, GL_FLOAT, 0, 0
            )
            glVertexArrayFogCoordOffsetEXT(vao, buf, GL_FLOAT, 0, 0)
            glVertexArraySecondaryColorOffsetEXT(vao, buf, 3, GL_FLOAT, 0, 0)
        self.check_error('dsa vertex array legacy offsets')

    def _uniform_program(self):
        return self.compile_program(VS, FS)

    def test_program_uniform(self):
        self.require()
        with self.allow_missing():
            p = self._uniform_program()
            def L(n):
                return glGetUniformLocation(p, n)
            glProgramUniform1fEXT(p, L('uf'), 1)
            glProgramUniform1fvEXT(p, L('uf'), 1, np.ones(1, 'f'))
            glProgramUniform2fEXT(p, L('uv2'), 1, 2)
            glProgramUniform2fvEXT(p, L('uv2'), 1, np.ones(2, 'f'))
            glProgramUniform3fEXT(p, L('uv3'), 1, 2, 3)
            glProgramUniform3fvEXT(p, L('uv3'), 1, np.ones(3, 'f'))
            glProgramUniform4fEXT(p, L('uv4'), 1, 2, 3, 4)
            glProgramUniform4fvEXT(p, L('uv4'), 1, np.ones(4, 'f'))
            glProgramUniform1iEXT(p, L('ui'), 1)
            glProgramUniform1ivEXT(p, L('ui'), 1, np.ones(1, 'i'))
            glProgramUniform2iEXT(p, L('ui2'), 1, 2)
            glProgramUniform2ivEXT(p, L('ui2'), 1, np.ones(2, 'i'))
            glProgramUniform3iEXT(p, L('ui3'), 1, 2, 3)
            glProgramUniform3ivEXT(p, L('ui3'), 1, np.ones(3, 'i'))
            glProgramUniform4iEXT(p, L('ui4'), 1, 2, 3, 4)
            glProgramUniform4ivEXT(p, L('ui4'), 1, np.ones(4, 'i'))
            glProgramUniform1uiEXT(p, L('uu'), 1)
            glProgramUniform1uivEXT(p, L('uu'), 1, np.ones(1, 'I'))
            glProgramUniform2uiEXT(p, L('uu2'), 1, 2)
            glProgramUniform2uivEXT(p, L('uu2'), 1, np.ones(2, 'I'))
            glProgramUniform3uiEXT(p, L('uu3'), 1, 2, 3)
            glProgramUniform3uivEXT(p, L('uu3'), 1, np.ones(3, 'I'))
            glProgramUniform4uiEXT(p, L('uu4'), 1, 2, 3, 4)
            glProgramUniform4uivEXT(p, L('uu4'), 1, np.ones(4, 'I'))
            glProgramUniform1dEXT(p, L('ud'), 1)
            glProgramUniform1dvEXT(p, L('ud'), 1, np.ones(1, 'd'))
            glProgramUniform2dEXT(p, L('ud2'), 1, 2)
            glProgramUniform2dvEXT(p, L('ud2'), 1, np.ones(2, 'd'))
            glProgramUniform3dEXT(p, L('ud3'), 1, 2, 3)
            glProgramUniform3dvEXT(p, L('ud3'), 1, np.ones(3, 'd'))
            glProgramUniform4dEXT(p, L('ud4'), 1, 2, 3, 4)
            glProgramUniform4dvEXT(p, L('ud4'), 1, np.ones(4, 'd'))
            glProgramUniformMatrix2fvEXT(p, L('m2'), 1, False, np.eye(2, dtype='f'))
            glProgramUniformMatrix3fvEXT(p, L('m3'), 1, False, np.eye(3, dtype='f'))
            glProgramUniformMatrix4fvEXT(p, L('m4'), 1, False, np.eye(4, dtype='f'))
            glProgramUniformMatrix2x3fvEXT(p, L('m23'), 1, False, np.zeros((2, 3), 'f'))
            glProgramUniformMatrix3x2fvEXT(p, L('m32'), 1, False, np.zeros((3, 2), 'f'))
            glProgramUniformMatrix2x4fvEXT(p, L('m24'), 1, False, np.zeros((2, 4), 'f'))
            glProgramUniformMatrix4x2fvEXT(p, L('m42'), 1, False, np.zeros((4, 2), 'f'))
            glProgramUniformMatrix3x4fvEXT(p, L('m34'), 1, False, np.zeros((3, 4), 'f'))
            glProgramUniformMatrix4x3fvEXT(p, L('m43'), 1, False, np.zeros((4, 3), 'f'))
            glProgramUniformMatrix2dvEXT(p, L('dm2'), 1, False, np.eye(2, dtype='d'))
            glProgramUniformMatrix3dvEXT(p, L('dm3'), 1, False, np.eye(3, dtype='d'))
            glProgramUniformMatrix4dvEXT(p, L('dm4'), 1, False, np.eye(4, dtype='d'))
            glProgramUniformMatrix2x3dvEXT(
                p, L('dm23'), 1, False, np.zeros((2, 3), 'd')
            )
            glProgramUniformMatrix3x2dvEXT(
                p, L('dm32'), 1, False, np.zeros((3, 2), 'd')
            )
            glProgramUniformMatrix2x4dvEXT(
                p, L('dm24'), 1, False, np.zeros((2, 4), 'd')
            )
            glProgramUniformMatrix4x2dvEXT(
                p, L('dm42'), 1, False, np.zeros((4, 2), 'd')
            )
            glProgramUniformMatrix3x4dvEXT(
                p, L('dm34'), 1, False, np.zeros((3, 4), 'd')
            )
            glProgramUniformMatrix4x3dvEXT(
                p, L('dm43'), 1, False, np.zeros((4, 3), 'd')
            )
        self.check_error('dsa program uniform')

    def test_indexed_state(self):
        self.require()
        with self.allow_missing():
            glEnableIndexedEXT(GL_BLEND, 0)
            glIsEnabledIndexedEXT(GL_BLEND, 0)
            glDisableIndexedEXT(GL_BLEND, 0)
            glGetBooleanIndexedvEXT(GL_BLEND, 0, np.zeros(1, 'B'))
            glGetIntegerIndexedvEXT(GL_BLEND, 0, np.zeros(1, 'i'))
            glGetFloati_vEXT(GL_VIEWPORT, 0, np.zeros(4, 'f'))
            glGetDoublei_vEXT(GL_DEPTH_RANGE, 0, np.zeros(2, 'd'))
            glGetFloatIndexedvEXT(GL_VIEWPORT, 0, np.zeros(4, 'f'))
            glGetDoubleIndexedvEXT(GL_DEPTH_RANGE, 0, np.zeros(2, 'd'))
            glEnableClientStateiEXT(GL_TEXTURE_COORD_ARRAY, 0)
            glDisableClientStateiEXT(GL_TEXTURE_COORD_ARRAY, 0)
            glEnableClientStateIndexedEXT(GL_TEXTURE_COORD_ARRAY, 0)
            glDisableClientStateIndexedEXT(GL_TEXTURE_COORD_ARRAY, 0)
            glClientAttribDefaultEXT(GL_CLIENT_ALL_ATTRIB_BITS)
            glPushClientAttribDefaultEXT(GL_CLIENT_ALL_ATTRIB_BITS)
            glPopClientAttrib()
        self.check_error('dsa indexed state')
        # the indexed client-array pointer targets are not accepted here
        with self.exercise(
            'the indexed client-array pointer targets are not accepted here'
        ):
            ptr = ctypes.c_void_p()
            glGetPointeri_vEXT(GL_VERTEX_ARRAY_POINTER, 0, ctypes.byref(ptr))
            glGetPointerIndexedvEXT(GL_VERTEX_ARRAY_POINTER, 0, ctypes.byref(ptr))

    def test_named_program(self):
        self.require()
        self.require_extension('GL_ARB_vertex_program')
        from OpenGL.GL.ARB.vertex_program import (
            glGenProgramsARB,
            GL_VERTEX_PROGRAM_ARB,
            GL_PROGRAM_FORMAT_ASCII_ARB,
            GL_PROGRAM_LENGTH_ARB,
            GL_PROGRAM_STRING_ARB,
        )

        T = GL_VERTEX_PROGRAM_ARB
        src = b'!!ARBvp1.0\nMOV result.position, vertex.position;\nEND'
        with self.allow_missing():
            pid = one(glGenProgramsARB(1))
            glNamedProgramStringEXT(pid, T, GL_PROGRAM_FORMAT_ASCII_ARB, len(src), src)
            glNamedProgramLocalParameter4fEXT(pid, T, 0, 1, 2, 3, 4)
            glNamedProgramLocalParameter4fvEXT(pid, T, 1, np.array([1, 2, 3, 4], 'f'))
            glNamedProgramLocalParameter4dEXT(pid, T, 0, 1, 2, 3, 4)
            glNamedProgramLocalParameter4dvEXT(pid, T, 1, np.array([1, 2, 3, 4], 'd'))
            glNamedProgramLocalParameters4fvEXT(
                pid, T, 0, 1, np.array([1, 2, 3, 4], 'f')
            )
            glGetNamedProgramLocalParameterfvEXT(pid, T, 0, np.zeros(4, 'f'))
            glGetNamedProgramLocalParameterdvEXT(pid, T, 0, np.zeros(4, 'd'))
            glGetNamedProgramivEXT(pid, T, GL_PROGRAM_LENGTH_ARB, np.zeros(1, 'i'))
            glGetNamedProgramStringEXT(
                pid, T, GL_PROGRAM_STRING_ARB, (ctypes.c_char * len(src))()
            )
        # NV_gpu_program4 integer local-params -- exercise the wrappers (driver
        # may lack the program target; exercise() tolerates the GLError)
        with self.allow_missing():
            glNamedProgramLocalParameterI4iEXT(pid, T, 0, 1, 2, 3, 4)
            glNamedProgramLocalParameterI4ivEXT(pid, T, 1, np.array([1, 2, 3, 4], 'i'))
            glNamedProgramLocalParameterI4uiEXT(pid, T, 0, 1, 2, 3, 4)
            glNamedProgramLocalParameterI4uivEXT(pid, T, 1, np.array([1, 2, 3, 4], 'I'))
            glNamedProgramLocalParametersI4ivEXT(
                pid, T, 0, 1, np.array([1, 2, 3, 4], 'i')
            )
            glNamedProgramLocalParametersI4uivEXT(
                pid, T, 0, 1, np.array([1, 2, 3, 4], 'I')
            )
            glGetNamedProgramLocalParameterIivEXT(pid, T, 0, np.zeros(4, 'i'))
            glGetNamedProgramLocalParameterIuivEXT(pid, T, 0, np.zeros(4, 'I'))


if __name__ == '__main__':
    unittest.main()
