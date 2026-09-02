#! /usr/bin/env python3
"""Many small legacy/aliased extensions, grouped by the context they need.
Each method requires its extension and exercises the entry points; references
predate-core aliases of functions already covered by the version suites."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.vertex_buffer_object import *  # noqa: F401,F403
from OpenGL.GL.EXT.vertex_array import *  # noqa: F401,F403
from OpenGL.GL.ARB.occlusion_query import *  # noqa: F401,F403
from OpenGL.GL.ARB.texture_compression import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture_object import *  # noqa: F401,F403
from OpenGL.GL.EXT.fog_coord import *  # noqa: F401,F403
from OpenGL.GL.EXT.copy_texture import *  # noqa: F401,F403
from OpenGL.GL.ARB.transpose_matrix import *  # noqa: F401,F403
from OpenGL.GL.EXT.point_parameters import *  # noqa: F401,F403
from OpenGL.GL.ARB.point_parameters import glPointParameterfARB, glPointParameterfvARB  # noqa: F401
from OpenGL.GL.EXT.multi_draw_arrays import *  # noqa: F401,F403
from OpenGL.GL.IBM.multimode_draw_arrays import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture3D import *  # noqa: F401,F403
from OpenGL.GL.EXT.subtexture import *  # noqa: F401,F403
from OpenGL.GL.NV.primitive_restart import *  # noqa: F401,F403
from OpenGL.GL.EXT.gpu_program_parameters import *  # noqa: F401,F403
from OpenGL.GL.EXT.compiled_vertex_array import *  # noqa: F401,F403
from OpenGL.GL.ATI.separate_stencil import *  # noqa: F401,F403
from OpenGL.GL.ARB.color_buffer_float import *  # noqa: F401,F403
from OpenGL.GL.ARB.multisample import *  # noqa: F401,F403
from OpenGL.GL.ATI.draw_buffers import *  # noqa: F401,F403
from OpenGL.GL.EXT.blend_color import *  # noqa: F401,F403
from OpenGL.GL.EXT.blend_func_separate import *  # noqa: F401,F403
from OpenGL.GL.EXT.blend_minmax import *  # noqa: F401,F403
from OpenGL.GL.EXT.draw_range_elements import *  # noqa: F401,F403
from OpenGL.GL.EXT.stencil_two_side import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture_buffer_object import *  # noqa: F401,F403
from OpenGL.GL.INGR.blend_func_separate import *  # noqa: F401,F403


class TestLegacyCompat(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_vertex_buffer_object_arb(self):
        self.require_extension('GL_ARB_vertex_buffer_object')
        with self.allow_missing():
            buf = int(glGenBuffersARB(1))
            glBindBufferARB(GL_ARRAY_BUFFER, buf)
            self.assertTrue(glIsBufferARB(buf))
            glBufferDataARB(GL_ARRAY_BUFFER, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
            glBufferSubDataARB(GL_ARRAY_BUFFER, 0, 16, np.ones(4, 'f'))
            glGetBufferParameterivARB(GL_ARRAY_BUFFER, GL_BUFFER_SIZE, np.zeros(1, 'i'))
            glGetBufferSubDataARB(GL_ARRAY_BUFFER, 0, 16, np.zeros(16, 'B'))
            ptr = ctypes.c_void_p()
            glGetBufferPointervARB(
                GL_ARRAY_BUFFER, GL_BUFFER_MAP_POINTER, ctypes.byref(ptr)
            )
            glMapBufferARB(GL_ARRAY_BUFFER, GL_READ_ONLY)
            glUnmapBufferARB(GL_ARRAY_BUFFER)
            glDeleteBuffersARB(1, [buf])

    def test_vertex_array_ext(self):
        self.require_extension('GL_EXT_vertex_array')
        with self.allow_missing():
            verts = np.zeros((4, 3), 'f')
            glVertexPointerEXT(3, GL_FLOAT, 0, 4, verts)
            glColorPointerEXT(4, GL_FLOAT, 0, 4, np.zeros((4, 4), 'f'))
            glNormalPointerEXT(GL_FLOAT, 0, 4, np.zeros((4, 3), 'f'))
            glTexCoordPointerEXT(2, GL_FLOAT, 0, 4, np.zeros((4, 2), 'f'))
            glIndexPointerEXT(GL_FLOAT, 0, 4, np.zeros(4, 'f'))
            glEdgeFlagPointerEXT(0, 4, np.ones(4, 'B'))
            glEnableClientState(GL_VERTEX_ARRAY)
            glArrayElementEXT(0)
            glDrawArraysEXT(GL_POINTS, 0, 4)
            ptr = ctypes.c_void_p()
            glGetPointervEXT(GL_VERTEX_ARRAY_POINTER, ctypes.byref(ptr))
            glDisableClientState(GL_VERTEX_ARRAY)

    def test_occlusion_query_arb(self):
        self.require_extension('GL_ARB_occlusion_query')
        with self.allow_missing():
            q = int(glGenQueriesARB(1))
            glBeginQueryARB(GL_SAMPLES_PASSED, q)
            glEndQueryARB(GL_SAMPLES_PASSED)
            self.assertTrue(glIsQueryARB(q))  # only a query name once begun
            glGetQueryivARB(GL_SAMPLES_PASSED, GL_CURRENT_QUERY, np.zeros(1, 'i'))
            glGetQueryObjectivARB(q, GL_QUERY_RESULT, np.zeros(1, 'i'))
            glGetQueryObjectuivARB(q, GL_QUERY_RESULT, np.zeros(1, 'I'))
            glDeleteQueriesARB(1, [q])

    def test_texture_compression_arb(self):
        self.require_extension('GL_ARB_texture_compression')
        fmt = GL_COMPRESSED_RGB8_ETC2
        data = np.zeros(8, 'B')  # one ETC2 4x4 block; friendly form derives imageSize
        with self.allow_missing():
            tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, tex)
            glCompressedTexImage2DARB(GL_TEXTURE_2D, 0, fmt, 4, 4, 0, data)
            glCompressedTexSubImage2DARB(GL_TEXTURE_2D, 0, 0, 0, 4, 4, fmt, data)
            glGetCompressedTexImageARB(GL_TEXTURE_2D, 0, np.zeros(8, 'B'))
        # 1D/3D targets are not valid for ETC2; calls drive the wrappers and
        # exercise() tolerates the resulting GLError
        with self.exercise():
            glBindTexture(GL_TEXTURE_1D, int(glGenTextures(1)))
            glCompressedTexImage1DARB(GL_TEXTURE_1D, 0, fmt, 4, 0, data)
            glCompressedTexSubImage1DARB(GL_TEXTURE_1D, 0, 0, 4, fmt, data)
            glBindTexture(GL_TEXTURE_3D, int(glGenTextures(1)))
            glCompressedTexImage3DARB(GL_TEXTURE_3D, 0, fmt, 4, 4, 1, 0, data)
            glCompressedTexSubImage3DARB(GL_TEXTURE_3D, 0, 0, 0, 0, 4, 4, 1, fmt, data)

    def test_texture_object_ext(self):
        self.require_extension('GL_EXT_texture_object')
        with self.allow_missing():
            tex = int(glGenTexturesEXT(1))
            glBindTextureEXT(GL_TEXTURE_2D, tex)
            self.assertTrue(glIsTextureEXT(tex))
            glPrioritizeTexturesEXT(1, np.array([tex], 'I'), np.array([1.0], 'f'))
            res = np.zeros(1, 'B')
            glAreTexturesResidentEXT(1, np.array([tex], 'I'), res)
            glDeleteTexturesEXT(1, np.array([tex], 'I'))

    def test_fog_coord_ext(self):
        self.require_extension('GL_EXT_fog_coord')
        with self.allow_missing():
            glFogCoordfEXT(1.0)
            glFogCoorddEXT(1.0)
            glFogCoordfvEXT(np.ones(1, 'f'))
            glFogCoorddvEXT(np.ones(1, 'd'))
            buf = int(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, np.zeros(4, 'f'), GL_STATIC_DRAW)
            glFogCoordPointerEXT(GL_FLOAT, 0, None)

    def test_copy_texture_ext(self):
        self.require_extension('GL_EXT_copy_texture')
        with self.allow_missing():
            tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA8, 8, 8, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glCopyTexSubImage2DEXT(GL_TEXTURE_2D, 0, 0, 0, 0, 0, 4, 4)
            glCopyTexImage2DEXT(GL_TEXTURE_2D, 0, GL_RGBA8, 0, 0, 4, 4, 0)
            t1 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_1D, t1)
            glCopyTexImage1DEXT(GL_TEXTURE_1D, 0, GL_RGBA8, 0, 0, 4, 0)
            glCopyTexSubImage1DEXT(GL_TEXTURE_1D, 0, 0, 0, 0, 4)
            t3 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_3D, t3)
            glTexImage3D(
                GL_TEXTURE_3D, 0, GL_RGBA8, 4, 4, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glCopyTexSubImage3DEXT(GL_TEXTURE_3D, 0, 0, 0, 0, 0, 0, 4, 4)

    def test_transpose_matrix_arb(self):
        self.require_extension('GL_ARB_transpose_matrix')
        with self.allow_missing():
            glMatrixMode(GL_MODELVIEW)
            glLoadTransposeMatrixfARB(np.eye(4, dtype='f'))
            glLoadTransposeMatrixdARB(np.eye(4, dtype='d'))
            glMultTransposeMatrixfARB(np.eye(4, dtype='f'))
            glMultTransposeMatrixdARB(np.eye(4, dtype='d'))

    def test_point_parameters(self):
        self.require_extension('GL_ARB_point_parameters')
        with self.allow_missing():
            glPointParameterfARB(GL_POINT_SIZE_MIN, 1.0)
            glPointParameterfvARB(
                GL_POINT_DISTANCE_ATTENUATION, np.array([1, 0, 0], 'f')
            )
            glPointParameterfEXT(GL_POINT_SIZE_MIN, 1.0)
            glPointParameterfvEXT(
                GL_POINT_DISTANCE_ATTENUATION, np.array([1, 0, 0], 'f')
            )

    def test_multi_draw_arrays(self):
        self.require_extension('GL_EXT_multi_draw_arrays')
        with self.allow_missing():
            first = np.array([0], 'i')
            count = np.array([3], 'i')
            glMultiDrawArraysEXT(GL_TRIANGLES, first, count, 1)
            ebo = int(glGenBuffers(1))
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(
                GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW
            )
            offsets = (ctypes.c_void_p * 1)(0)  # byte offsets into bound EBO
            glMultiDrawElementsEXT(GL_TRIANGLES, count, GL_UNSIGNED_INT, offsets, 1)
            modes = np.array([GL_TRIANGLES], 'I')
            glMultiModeDrawArraysIBM(modes, first, count, 1, 0)
            glMultiModeDrawElementsIBM(modes, count, GL_UNSIGNED_INT, offsets, 1, 0)

    def test_texture3d_subtexture_ext(self):
        self.require_extension('GL_EXT_texture3D')
        with self.allow_missing():
            tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_3D, tex)
            px = np.zeros((2, 2, 2, 4), 'B')
            glTexImage3DEXT(
                GL_TEXTURE_3D, 0, GL_RGBA8, 2, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, px
            )
            glTexSubImage3DEXT(
                GL_TEXTURE_3D, 0, 0, 0, 0, 2, 2, 2, GL_RGBA, GL_UNSIGNED_BYTE, px
            )
            t2 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, t2)
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA8, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glTexSubImage2DEXT(
                GL_TEXTURE_2D,
                0,
                0,
                0,
                2,
                2,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                np.zeros((2, 2, 4), 'B'),
            )
            t1 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_1D, t1)
            glTexImage1D(
                GL_TEXTURE_1D, 0, GL_RGBA8, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glTexSubImage1DEXT(
                GL_TEXTURE_1D, 0, 0, 2, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros((2, 4), 'B')
            )

    def test_primitive_restart_nv(self):
        self.require_extension('GL_NV_primitive_restart')
        with self.allow_missing():
            glPrimitiveRestartIndexNV(0xFFFF)
            glEnableClientState(GL_PRIMITIVE_RESTART_NV)
            # glPrimitiveRestartNV is only valid inside a Begin/End block
            with self.begin(GL_TRIANGLE_STRIP):
                glPrimitiveRestartNV()
            glDisableClientState(GL_PRIMITIVE_RESTART_NV)

    def test_compiled_vertex_array_ext(self):
        self.require_extension('GL_EXT_compiled_vertex_array')
        with self.allow_missing():
            glVertexPointer(3, GL_FLOAT, 0, np.zeros((4, 3), 'f'))
            glEnableClientState(GL_VERTEX_ARRAY)
            glLockArraysEXT(0, 4)
            glUnlockArraysEXT()
            glDisableClientState(GL_VERTEX_ARRAY)

    def test_gpu_program_parameters_ext(self):
        self.require_extension('GL_EXT_gpu_program_parameters')
        self.require_extension('GL_ARB_vertex_program')
        from OpenGL.GL.ARB.vertex_program import GL_VERTEX_PROGRAM_ARB

        with self.allow_missing():
            glProgramEnvParameters4fvEXT(GL_VERTEX_PROGRAM_ARB, 0, 1, np.zeros(4, 'f'))
            glProgramLocalParameters4fvEXT(
                GL_VERTEX_PROGRAM_ARB, 0, 1, np.zeros(4, 'f')
            )

    def test_separate_stencil_ati(self):
        self.require_extension('GL_ATI_separate_stencil')
        with self.allow_missing():
            glStencilFuncSeparateATI(GL_ALWAYS, GL_ALWAYS, 0, 0xFF)
            glStencilOpSeparateATI(GL_FRONT, GL_KEEP, GL_KEEP, GL_KEEP)

    def test_clamp_color_arb(self):
        self.require_extension('GL_ARB_color_buffer_float')
        with self.allow_missing():
            glClampColorARB(GL_CLAMP_VERTEX_COLOR_ARB, GL_TRUE)  # the default

    def test_sample_coverage_arb(self):
        self.require_extension('GL_ARB_multisample')
        with self.allow_missing():
            glSampleCoverageARB(1.0, GL_FALSE)  # the default

    def test_draw_buffers_ati(self):
        self.require_extension('GL_ATI_draw_buffers')
        with self.allow_missing():
            # GL_BACK is not a valid glDrawBuffers entry pre-4.5; use BACK_LEFT
            glDrawBuffersATI(1, np.array([GL_BACK_LEFT], 'I'))

    def test_blend_color_ext(self):
        self.require_extension('GL_EXT_blend_color')
        with self.allow_missing():
            glBlendColorEXT(0.25, 0.5, 0.75, 1.0)
            glBlendColorEXT(0.0, 0.0, 0.0, 0.0)  # the default

    def test_blend_minmax_ext(self):
        self.require_extension('GL_EXT_blend_minmax')
        with self.allow_missing():
            glBlendEquationEXT(GL_MIN_EXT)
            glBlendEquationEXT(GL_MAX_EXT)
            glBlendEquationEXT(GL_FUNC_ADD_EXT)  # the default

    def test_blend_func_separate_ext(self):
        self.require_extension('GL_EXT_blend_func_separate')
        with self.allow_missing():
            glBlendFuncSeparateEXT(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ZERO)
            glBlendFunc(GL_ONE, GL_ZERO)  # back to the default

    def test_blend_func_separate_ingr(self):
        self.require_extension('GL_INGR_blend_func_separate')
        with self.allow_missing():
            # INGR variant only guarantees a restricted factor subset; ONE/ZERO
            # are valid in both it and the EXT version it aliases
            glBlendFuncSeparateINGR(GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)

    def test_draw_range_elements_ext(self):
        self.require_extension('GL_EXT_draw_range_elements')
        with self.allow_missing():
            glVertexPointer(3, GL_FLOAT, 0, np.zeros((3, 3), 'f'))
            glEnableClientState(GL_VERTEX_ARRAY)
            glDrawRangeElementsEXT(
                GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, np.array([0, 1, 2], 'I')
            )
            glDisableClientState(GL_VERTEX_ARRAY)

    def test_stencil_two_side_ext(self):
        self.require_extension('GL_EXT_stencil_two_side')
        with self.allow_missing():
            glEnable(GL_STENCIL_TEST_TWO_SIDE_EXT)
            glActiveStencilFaceEXT(GL_BACK)
            glActiveStencilFaceEXT(GL_FRONT)
            glDisable(GL_STENCIL_TEST_TWO_SIDE_EXT)

    def test_texture_buffer_object_ext(self):
        self.require_extension('GL_EXT_texture_buffer_object')
        with self.allow_missing():
            buf = int(glGenBuffers(1))
            glBindBuffer(GL_TEXTURE_BUFFER_EXT, buf)
            glBufferData(GL_TEXTURE_BUFFER_EXT, np.zeros(16, 'f'), GL_STATIC_DRAW)
            tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_BUFFER_EXT, tex)
            glTexBufferEXT(GL_TEXTURE_BUFFER_EXT, GL_RGBA32F, buf)
            glTexBufferEXT(GL_TEXTURE_BUFFER_EXT, GL_RGBA32F, 0)  # detach
            glBindBuffer(GL_TEXTURE_BUFFER_EXT, 0)


if __name__ == '__main__':
    unittest.main()
