#! /usr/bin/env python3
"""Core-context legacy/aliased extensions: transform feedback, integer texture
params, shading-language include, debug-output, indexed blend, conditional
render, timer query, instanced draws, KHR_debug aliases and assorted singles."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.EXT.transform_feedback import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture_integer import *  # noqa: F401,F403
from OpenGL.GL.ARB.shading_language_include import *  # noqa: F401,F403
from OpenGL.GL.ARB.debug_output import *  # noqa: F401,F403
from OpenGL.GL.ARB.draw_buffers_blend import *  # noqa: F401,F403
from OpenGL.GL.AMD.draw_buffers_blend import *  # noqa: F401,F403
from OpenGL.GL.NV.conditional_render import *  # noqa: F401,F403
from OpenGL.GL.EXT.timer_query import *  # noqa: F401,F403
from OpenGL.GL.EXT.draw_instanced import *  # noqa: F401,F403
from OpenGL.GL.ARB.draw_instanced import (
    glDrawArraysInstancedARB,
    glDrawElementsInstancedARB,
)  # noqa: F401
from OpenGL.GL.EXT.debug_label import *  # noqa: F401,F403
from OpenGL.GL.KHR.debug import *  # noqa: F401,F403
from OpenGL.GL.MESA.framebuffer_flip_y import *  # noqa: F401,F403
from OpenGL.GL.OVR.multiview import *  # noqa: F401,F403
from OpenGL.GL.AMD.multi_draw_indirect import *  # noqa: F401,F403
from OpenGL.GL.ARB.indirect_parameters import *  # noqa: F401,F403
from OpenGL.GL.ARB.instanced_arrays import *  # noqa: F401,F403
from OpenGL.GL.ARB.draw_buffers import *  # noqa: F401,F403
from OpenGL.GL.EXT.draw_buffers2 import *  # noqa: F401,F403
from OpenGL.GL.EXT.blend_equation_separate import *  # noqa: F401,F403
from OpenGL.GL.KHR.blend_equation_advanced import *  # noqa: F401,F403
from OpenGL.GL.NV.alpha_to_coverage_dither_control import *  # noqa: F401,F403
from OpenGL.GL.ARB.texture_buffer_object import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture_storage import *  # noqa: F401,F403
from OpenGL.GL.EXT.EGL_image_storage import *  # noqa: F401,F403
from OpenGL.GL.NV.copy_image import *  # noqa: F401,F403
from OpenGL.GL.NV.texture_barrier import *  # noqa: F401,F403
from OpenGL.GL.ARB.parallel_shader_compile import *  # noqa: F401,F403
from OpenGL.GL.KHR.parallel_shader_compile import *  # noqa: F401,F403
from OpenGL.GL.ARB.gl_spirv import *  # noqa: F401,F403
from OpenGL.GL.EXT.shader_framebuffer_fetch_non_coherent import *  # noqa: F401,F403
from OpenGL.GL.ARB.sample_shading import *  # noqa: F401,F403
from OpenGL.GL.EXT.provoking_vertex import *  # noqa: F401,F403
from OpenGL.GL.EXT.polygon_offset_clamp import *  # noqa: F401,F403
from OpenGL.GL.ARB.ES3_2_compatibility import *  # noqa: F401,F403
from OpenGL.GL.ARB.viewport_array import (
    glDepthRangeArraydvNV,
    glDepthRangeIndexeddNV,
)  # noqa: F401

VS = '#version 150\nin vec4 p; out float v; void main(){ v = p.x; gl_Position = p; }'
FS = '#version 150\nout vec4 c; void main(){ c = vec4(1.0); }'


def _first(ids):
    return int(ids[0]) if hasattr(ids, '__len__') else int(ids)


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*strings)
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestMiscCore(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_transform_feedback_ext(self):
        self.require_extension('GL_EXT_transform_feedback')
        with self.allow_missing():
            from OpenGL.GL import shaders

            vs = shaders.compileShader(VS, GL_VERTEX_SHADER)
            fs = shaders.compileShader(FS, GL_FRAGMENT_SHADER)
            prog = glCreateProgram()
            glAttachShader(prog, vs)
            glAttachShader(prog, fs)
            glTransformFeedbackVaryingsEXT(
                prog, 1, _char_pp([b'v']), GL_INTERLEAVED_ATTRIBS
            )
            glLinkProgram(prog)
            glUseProgram(prog)
            glGetTransformFeedbackVaryingEXT(
                prog,
                0,
                64,
                np.zeros(1, 'i'),
                np.zeros(1, 'i'),
                np.zeros(1, 'I'),
                (ctypes.c_char * 64)(),
            )
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, buf)
            glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 64, None, GL_DYNAMIC_DRAW)
            glBindBufferBaseEXT(GL_TRANSFORM_FEEDBACK_BUFFER, 0, buf)
            glBindBufferRangeEXT(GL_TRANSFORM_FEEDBACK_BUFFER, 0, buf, 0, 64)
            glBindBufferOffsetEXT(GL_TRANSFORM_FEEDBACK_BUFFER, 0, buf, 0)
            glBeginTransformFeedbackEXT(GL_POINTS)
            glEndTransformFeedbackEXT()

    def test_texture_integer_ext(self):
        self.require_extension('GL_EXT_texture_integer')
        with self.allow_missing():
            tex = one(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameterIivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i')
            )
            glTexParameterIuivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I')
            )
            glGetTexParameterIivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i')
            )
            glGetTexParameterIuivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I')
            )
            glClearColorIiEXT(0, 0, 0, 0)
            glClearColorIuiEXT(0, 0, 0, 0)

    def test_shading_language_include_arb(self):
        self.require_extension('GL_ARB_shading_language_include')
        with self.allow_missing():
            name = b'/inc.glsl'
            body = b'float k(){ return 1.0; }'
            glNamedStringARB(GL_SHADER_INCLUDE_ARB, len(name), name, len(body), body)
            self.assertTrue(glIsNamedStringARB(len(name), name))
            glGetNamedStringARB(
                len(name), name, 256, np.zeros(1, 'i'), (ctypes.c_char * 256)()
            )
            glGetNamedStringivARB(
                len(name), name, GL_NAMED_STRING_LENGTH_ARB, np.zeros(1, 'i')
            )
            glDeleteNamedStringARB(len(name), name)
        # glCompileShaderIncludeARB's include-path tree validation is finicky;
        # the call drives the wrapper and exercise() tolerates the GLError
        with self.exercise():
            sh = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(
                sh,
                '#version 420\n#extension GL_ARB_shading_language_include : require\n'
                '#include "/inc.glsl"\nout vec4 c; void main(){ c = vec4(1.0); }',
            )
            glCompileShaderIncludeARB(sh, 1, _char_pp([b'/']), None)

    def test_debug_output_arb(self):
        self.require_extension('GL_ARB_debug_output')
        with self.allow_missing():

            @GLDEBUGPROCARB
            def cb(source, t, i, sev, length, message, user):
                return None

            self._cb = cb
            glDebugMessageCallbackARB(cb, None)
            glDebugMessageControlARB(
                GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, None, GL_TRUE
            )
            glDebugMessageInsertARB(
                GL_DEBUG_SOURCE_APPLICATION_ARB,
                GL_DEBUG_TYPE_OTHER_ARB,
                1,
                GL_DEBUG_SEVERITY_LOW_ARB,
                -1,
                b'hi',
            )
            glGetDebugMessageLogARB(
                4,
                256,
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'i'),
                (ctypes.c_char * 256)(),
            )

    def test_indexed_blend(self):
        self.require_extension('GL_ARB_draw_buffers_blend')
        with self.allow_missing():
            glBlendEquationiARB(0, GL_FUNC_ADD)
            glBlendEquationSeparateiARB(0, GL_FUNC_ADD, GL_FUNC_ADD)
            glBlendFunciARB(0, GL_ONE, GL_ZERO)
            glBlendFuncSeparateiARB(0, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
        with self.allow_missing():
            self.require_extension('GL_AMD_draw_buffers_blend')
            glBlendEquationIndexedAMD(0, GL_FUNC_ADD)
            glBlendEquationSeparateIndexedAMD(0, GL_FUNC_ADD, GL_FUNC_ADD)
            glBlendFuncIndexedAMD(0, GL_ONE, GL_ZERO)
            glBlendFuncSeparateIndexedAMD(0, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)

    def test_conditional_render_nv(self):
        self.require_extension('GL_NV_conditional_render')
        with self.allow_missing():
            q = _first(one(glGenQueries(1)))
            glBeginQuery(GL_SAMPLES_PASSED, q)
            glEndQuery(GL_SAMPLES_PASSED)
            glBeginConditionalRenderNV(q, GL_QUERY_WAIT_NV)
            glEndConditionalRenderNV()

    def test_timer_query_ext(self):
        self.require_extension('GL_EXT_timer_query')
        with self.allow_missing():
            q = _first(one(glGenQueries(1)))
            glBeginQuery(GL_TIME_ELAPSED, q)
            glEndQuery(GL_TIME_ELAPSED)
            glGetQueryObjecti64vEXT(q, GL_QUERY_RESULT, np.zeros(1, 'q'))
            glGetQueryObjectui64vEXT(q, GL_QUERY_RESULT, np.zeros(1, 'Q'))

    def test_draw_instanced(self):
        self.require_extension('GL_EXT_draw_instanced')
        with self.allow_missing():
            prog = self.compile_program(
                '#version 150\nin vec4 p; void main(){ gl_Position = p; }', FS
            )
            glUseProgram(prog)
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(
                GL_ARRAY_BUFFER,
                np.array([(-1, -1), (1, -1), (0, 1)], 'f'),
                GL_STATIC_DRAW,
            )
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
            glDrawArraysInstancedEXT(GL_TRIANGLES, 0, 3, 2)
            idx = np.array([0, 1, 2], 'I')
            ibo = one(glGenBuffers(1))
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, idx, GL_STATIC_DRAW)
            glDrawElementsInstancedEXT(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2)
            glDrawArraysInstancedARB(GL_TRIANGLES, 0, 3, 2)
            glDrawElementsInstancedARB(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2)

    def test_debug_label_ext(self):
        self.require_extension('GL_EXT_debug_label')
        with self.allow_missing():
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glLabelObjectEXT(
                GL_BUFFER_OBJECT_EXT, buf, 0, b'mybuf'
            )  # EXT length 0 = null-terminated
            glGetObjectLabelEXT(
                GL_BUFFER_OBJECT_EXT, buf, 64, np.zeros(1, 'i'), (ctypes.c_char * 64)()
            )

    def test_khr_debug_aliases(self):
        self.require_extension('GL_KHR_debug')
        with self.allow_missing():

            @GLDEBUGPROC
            def cb(source, t, i, sev, length, message, user):
                return None

            self._cb = cb
            glDebugMessageCallbackKHR(cb, None)
            glDebugMessageControlKHR(
                GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, None, GL_TRUE
            )
            glDebugMessageInsertKHR(
                GL_DEBUG_SOURCE_APPLICATION,
                GL_DEBUG_TYPE_OTHER,
                1,
                GL_DEBUG_SEVERITY_NOTIFICATION,
                -1,
                b'hi',
            )
            glPushDebugGroupKHR(GL_DEBUG_SOURCE_APPLICATION, 0, -1, b'g')
            glPopDebugGroupKHR()
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glObjectLabelKHR(GL_BUFFER, buf, -1, b'l')
            glGetObjectLabelKHR(
                GL_BUFFER, buf, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )
            sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
            glObjectPtrLabelKHR(sync, -1, b's')
            glGetObjectPtrLabelKHR(
                sync, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )
            ptr = ctypes.c_void_p()
            glGetPointervKHR(GL_DEBUG_CALLBACK_FUNCTION, ctypes.byref(ptr))
            glDeleteSync(sync)
            glGetDebugMessageLogKHR(
                4,
                256,
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'i'),
                (ctypes.c_char * 256)(),
            )

    def test_framebuffer_flip_y_mesa(self):
        self.require_extension('GL_MESA_framebuffer_flip_y')
        with self.allow_missing():
            fbo = one(glGenFramebuffers(1))
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferParameteriMESA(
                GL_FRAMEBUFFER, GL_FRAMEBUFFER_FLIP_Y_MESA, GL_TRUE
            )
            glGetFramebufferParameterivMESA(
                GL_FRAMEBUFFER, GL_FRAMEBUFFER_FLIP_Y_MESA, np.zeros(1, 'i')
            )

    def test_multiview_ovr(self):
        self.require_extension('GL_OVR_multiview')
        with self.allow_missing():
            arr = one(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D_ARRAY, arr)
            glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 16, 16, 2)
            fbo = one(glGenFramebuffers(1))
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTextureMultiviewOVR(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, arr, 0, 0, 2
            )
        # the DSA multiview form is not implemented here; the call drives the
        # wrapper and exercise() tolerates the GLError
        with self.exercise():
            glNamedFramebufferTextureMultiviewOVR(
                one(glGenFramebuffers(1)), GL_COLOR_ATTACHMENT0, arr, 0, 0, 2
            )


class TestDrawExtensions(GLTestCase):
    """Indirect / count / instanced / multi draw-buffer entry points carried by
    AMD and ARB/EXT aliases of core 4.x drawing commands."""

    profile = 'core'
    gl_version = (4, 5)

    def test_amd_multi_draw_indirect(self):
        self.require_extension('GL_AMD_multi_draw_indirect')
        # DrawArraysIndirectCommand: count, primCount, first, baseInstance
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, buf)
        glBufferData(GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0], 'I'), GL_STATIC_DRAW)
        with self.exercise():
            glMultiDrawArraysIndirectAMD(GL_TRIANGLES, None, 1, 0)
        # DrawElementsIndirectCommand: count, primCount, firstIndex, baseVertex, baseInstance
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0, 0], 'I'), GL_STATIC_DRAW
        )
        ibo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        with self.exercise():
            glMultiDrawElementsIndirectAMD(GL_TRIANGLES, GL_UNSIGNED_INT, None, 1, 0)

    def test_arb_indirect_parameters(self):
        self.require_extension('GL_ARB_indirect_parameters')
        dib = one(glGenBuffers(1))
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, dib)
        glBufferData(GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0], 'I'), GL_STATIC_DRAW)
        # GL_PARAMETER_BUFFER_ARB supplies the GPU-side draw count.
        pbuf = one(glGenBuffers(1))
        glBindBuffer(GL_PARAMETER_BUFFER_ARB, pbuf)
        glBufferData(GL_PARAMETER_BUFFER_ARB, np.array([1], 'I'), GL_STATIC_DRAW)
        with self.exercise():
            glMultiDrawArraysIndirectCountARB(GL_TRIANGLES, None, 0, 1, 0)
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0, 0], 'I'), GL_STATIC_DRAW
        )
        ibo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        with self.exercise():
            glMultiDrawElementsIndirectCountARB(
                GL_TRIANGLES, GL_UNSIGNED_INT, None, 0, 1, 0
            )

    def test_arb_instanced_arrays(self):
        self.require_extension('GL_ARB_instanced_arrays')
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(8, 'f'), GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        with self.allow_missing():
            glVertexAttribDivisorARB(0, 1)
        self.check_error('glVertexAttribDivisorARB')

    def test_arb_draw_buffers(self):
        self.require_extension('GL_ARB_draw_buffers')
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        with self.allow_missing():
            glDrawBuffersARB(1, np.array([GL_NONE], 'I'))
        self.check_error('glDrawBuffersARB')

    def test_ext_draw_buffers2_colormask(self):
        self.require_extension('GL_EXT_draw_buffers2')
        with self.allow_missing():
            glColorMaskIndexedEXT(0, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        self.check_error('glColorMaskIndexedEXT')


class TestBlendExtensions(GLTestCase):
    """Blend-equation aliases / barriers and alpha-to-coverage dithering."""

    profile = 'core'
    gl_version = (4, 5)

    def test_ext_blend_equation_separate(self):
        self.require_extension('GL_EXT_blend_equation_separate')
        with self.allow_missing():
            glBlendEquationSeparateEXT(GL_FUNC_ADD, GL_FUNC_ADD)
        self.check_error('glBlendEquationSeparateEXT')

    def test_khr_blend_equation_advanced_barrier(self):
        self.require_extension('GL_KHR_blend_equation_advanced')
        with self.exercise():
            glBlendBarrierKHR()

    def test_nv_alpha_to_coverage_dither_control(self):
        self.require_extension('GL_NV_alpha_to_coverage_dither_control')
        with self.exercise():
            glAlphaToCoverageDitherControlNV(GL_ALPHA_TO_COVERAGE_DITHER_DEFAULT_NV)


class TestTextureExtensions(GLTestCase):
    """Texture-buffer / immutable-storage aliases, image copies and barriers."""

    profile = 'core'
    gl_version = (4, 5)

    def test_arb_texture_buffer_object(self):
        self.require_extension('GL_ARB_texture_buffer_object')
        tbuf = one(glGenBuffers(1))
        glBindBuffer(GL_TEXTURE_BUFFER, tbuf)
        glBufferData(GL_TEXTURE_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_BUFFER, tex)
        with self.allow_missing():
            glTexBufferARB(GL_TEXTURE_BUFFER, GL_RGBA32F, tbuf)
        self.check_error('glTexBufferARB')

    def test_ext_texture_storage(self):
        self.require_extension('GL_EXT_texture_storage')
        glBindTexture(GL_TEXTURE_1D, one(glGenTextures(1)))
        glBindTexture(GL_TEXTURE_2D, one(glGenTextures(1)))
        glBindTexture(GL_TEXTURE_3D, one(glGenTextures(1)))
        with self.exercise():
            glTexStorage1DEXT(GL_TEXTURE_1D, 1, GL_RGBA8, 16)
            glTexStorage2DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
            glTexStorage3DEXT(GL_TEXTURE_3D, 1, GL_RGBA8, 16, 16, 16)

    def test_ext_egl_image_storage(self):
        self.require_extension('GL_EXT_EGL_image_storage')
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        # No EGLImage is available headless; a null image GLErrors, tolerated here.
        with self.exercise():
            glEGLImageTargetTexStorageEXT(GL_TEXTURE_2D, None, None)
        with self.exercise():
            glEGLImageTargetTextureStorageEXT(tex, None, None)

    def test_nv_copy_image(self):
        self.require_extension('GL_NV_copy_image')
        src = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, src)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        dst = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, dst)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        with self.exercise():
            glCopyImageSubDataNV(
                src, GL_TEXTURE_2D, 0, 0, 0, 0,
                dst, GL_TEXTURE_2D, 0, 0, 0, 0,
                16, 16, 1,
            )

    def test_nv_texture_barrier(self):
        self.require_extension('GL_NV_texture_barrier')
        with self.exercise():
            glTextureBarrierNV()


class TestShaderCompileExtensions(GLTestCase):
    """Parallel-compile hints, SPIR-V specialisation and the fetch barrier."""

    profile = 'core'
    gl_version = (4, 5)

    def test_arb_parallel_shader_compile(self):
        self.require_extension('GL_ARB_parallel_shader_compile')
        with self.allow_missing():
            glMaxShaderCompilerThreadsARB(2)
        self.check_error('glMaxShaderCompilerThreadsARB')

    def test_khr_parallel_shader_compile(self):
        self.require_extension('GL_KHR_parallel_shader_compile')
        with self.allow_missing():
            glMaxShaderCompilerThreadsKHR(2)
        self.check_error('glMaxShaderCompilerThreadsKHR')

    def test_arb_gl_spirv(self):
        self.require_extension('GL_ARB_gl_spirv')
        # No SPIR-V binary is loaded, so specialisation GLErrors; the call still
        # drives the wrapper's argument marshalling, which is what we cover here.
        with self.exercise():
            sh = glCreateShader(GL_FRAGMENT_SHADER)
            glSpecializeShaderARB(sh, b'main', 0, np.zeros(0, 'I'), np.zeros(0, 'I'))

    def test_ext_shader_framebuffer_fetch_non_coherent(self):
        self.require_extension('GL_EXT_shader_framebuffer_fetch_non_coherent')
        with self.exercise():
            glFramebufferFetchBarrierEXT()


class TestStateExtensions(GLTestCase):
    """Assorted per-context state setters: sample shading, provoking vertex,
    polygon-offset clamp, primitive bounding box and double-precision viewport
    depth-range aliases."""

    profile = 'core'
    gl_version = (4, 5)

    def test_arb_sample_shading(self):
        self.require_extension('GL_ARB_sample_shading')
        with self.allow_missing():
            glMinSampleShadingARB(1.0)
        self.check_error('glMinSampleShadingARB')

    def test_ext_provoking_vertex(self):
        self.require_extension('GL_EXT_provoking_vertex')
        with self.allow_missing():
            glProvokingVertexEXT(GL_LAST_VERTEX_CONVENTION)
        self.check_error('glProvokingVertexEXT')

    def test_ext_polygon_offset_clamp(self):
        self.require_extension('GL_EXT_polygon_offset_clamp')
        with self.allow_missing():
            glPolygonOffsetClampEXT(1.0, 1.0, 0.0)
        self.check_error('glPolygonOffsetClampEXT')

    def test_arb_es3_2_compatibility_bbox(self):
        self.require_extension('GL_ARB_ES3_2_compatibility')
        with self.allow_missing():
            glPrimitiveBoundingBoxARB(-1, -1, -1, 1, 1, 1, 1, 1)
        self.check_error('glPrimitiveBoundingBoxARB')

    def test_arb_viewport_array_double(self):
        self.require_extension('GL_ARB_viewport_array')
        with self.allow_missing():
            glDepthRangeArraydvNV(0, 1, np.array([0.0, 1.0], 'd'))
            glDepthRangeIndexeddNV(0, 0.0, 1.0)
        self.check_error('GL_ARB_viewport_array double-precision aliases')


if __name__ == '__main__':
    unittest.main()
