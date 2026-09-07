#! /usr/bin/env python3
"""ARB desktop-GL extensions that the NVIDIA driver exposes beyond the Mesa
baseline: bindless texture/image handles, sparse buffers/textures, sample
locations, the imaging subset, ARB geometry-shader4 framebuffer attach, and
variable-group-size compute.

These are functional tests -- they create real objects and make the actual
calls, asserting a clean GL error state -- not entry-point reachability probes.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403


class TestARBExtra(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    # --- GL_ARB_bindless_texture -----------------------------------------
    def test_arb_bindless_texture(self):
        self.require_extension('GL_ARB_bindless_texture')
        from OpenGL.GL.ARB.bindless_texture import (
            glGetTextureHandleARB,
            glGetTextureSamplerHandleARB,
            glMakeTextureHandleResidentARB,
            glMakeTextureHandleNonResidentARB,
            glIsTextureHandleResidentARB,
            glGetImageHandleARB,
            glMakeImageHandleResidentARB,
            glMakeImageHandleNonResidentARB,
            glIsImageHandleResidentARB,
            glUniformHandleui64ARB,
            glUniformHandleui64vARB,
            glProgramUniformHandleui64ARB,
            glProgramUniformHandleui64vARB,
            glVertexAttribL1ui64ARB,
            glVertexAttribL1ui64vARB,
            glGetVertexAttribLui64vARB,
        )

        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        sampler = one(glGenSamplers(1))
        glSamplerParameteri(sampler, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        handle = one(glGetTextureHandleARB(tex))
        self.assertTrue(handle)
        shandle = one(glGetTextureSamplerHandleARB(tex, sampler))
        self.assertTrue(shandle)
        glMakeTextureHandleResidentARB(handle)
        self.assertTrue(glIsTextureHandleResidentARB(handle))
        glMakeTextureHandleNonResidentARB(handle)

        img = one(glGetImageHandleARB(tex, 0, GL_FALSE, 0, GL_RGBA8))
        self.assertTrue(img)
        glMakeImageHandleResidentARB(img, GL_READ_ONLY)
        self.assertTrue(glIsImageHandleResidentARB(img))
        glMakeImageHandleNonResidentARB(img)

        # The uniform-handle setters take a *bindless* sampler uniform.  A
        # sampler declared without the layout qualifier is a bound one, whose
        # value is a texture image unit, and handing it a handle is an
        # INVALID_OPERATION -- the extension spec makes the qualifier what
        # decides, and only a driver defaulting the other way lets it pass.
        program = self.compile_program(
            '#version 450 core\nvoid main(){gl_Position=vec4(0.0);}',
            '#version 450 core\n'
            '#extension GL_ARB_bindless_texture : require\n'
            'layout(bindless_sampler) uniform sampler2D s; out vec4 c;\n'
            'void main(){ c = texture(s, vec2(0.5)); }',
        )
        loc = glGetUniformLocation(program, 's')
        glMakeTextureHandleResidentARB(handle)
        glUseProgram(program)
        glUniformHandleui64ARB(loc, handle)
        glUniformHandleui64vARB(loc, 1, np.array([handle], 'uint64'))
        glProgramUniformHandleui64ARB(program, loc, handle)
        glProgramUniformHandleui64vARB(program, loc, 1, np.array([handle], 'uint64'))
        glUseProgram(0)
        glMakeTextureHandleNonResidentARB(handle)

        # uint64 generic vertex attribute round-trip
        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        glVertexAttribL1ui64ARB(1, handle)
        glVertexAttribL1ui64vARB(1, np.array([handle], 'uint64'))
        # GL_CURRENT_VERTEX_ATTRIB always returns a 4-component value
        got = np.zeros(4, 'uint64')
        glGetVertexAttribLui64vARB(1, GL_CURRENT_VERTEX_ATTRIB, got)
        glBindVertexArray(0)
        self.check_error('arb bindless texture')

    # --- GL_ARB_compute_variable_group_size ------------------------------
    def test_arb_compute_variable_group_size(self):
        self.require_extension('GL_ARB_compute_variable_group_size')
        from OpenGL.GL.ARB.compute_variable_group_size import (
            glDispatchComputeGroupSizeARB,
        )

        source = (
            '#version 450 core\n'
            '#extension GL_ARB_compute_variable_group_size : require\n'
            'layout(local_size_variable) in;\n'
            'layout(std430, binding=0) buffer B { uint v[]; };\n'
            'void main(){ v[gl_GlobalInvocationID.x] = gl_LocalGroupSizeARB.x; }'
        )
        from OpenGL.GL import shaders, GL_COMPUTE_SHADER

        program = shaders.compileProgram(
            shaders.compileShader(source, GL_COMPUTE_SHADER)
        )
        ssbo = one(glGenBuffers(1))
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)
        glBufferData(GL_SHADER_STORAGE_BUFFER, 256, None, GL_DYNAMIC_DRAW)
        glUseProgram(program)
        glDispatchComputeGroupSizeARB(1, 1, 1, 4, 1, 1)
        glUseProgram(0)
        self.check_error('arb compute variable group size')

    # --- GL_ARB_geometry_shader4 -----------------------------------------
    def test_arb_geometry_shader4(self):
        self.require_extension('GL_ARB_geometry_shader4')
        from OpenGL.GL.ARB.geometry_shader4 import (
            glProgramParameteriARB,
            glFramebufferTextureARB,
            glFramebufferTextureLayerARB,
            glFramebufferTextureFaceARB,
            GL_GEOMETRY_VERTICES_OUT_ARB,
            GL_GEOMETRY_INPUT_TYPE_ARB,
            GL_GEOMETRY_OUTPUT_TYPE_ARB,
        )

        program = int(glCreateProgram())
        glProgramParameteriARB(program, GL_GEOMETRY_VERTICES_OUT_ARB, 3)
        glProgramParameteriARB(program, GL_GEOMETRY_INPUT_TYPE_ARB, GL_POINTS)
        glProgramParameteriARB(program, GL_GEOMETRY_OUTPUT_TYPE_ARB, GL_TRIANGLE_STRIP)

        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        flat = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, flat)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        glFramebufferTextureARB(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, flat, 0)

        layered = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_ARRAY, layered)
        glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 4, 4, 2)
        glFramebufferTextureLayerARB(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, layered, 0, 1)

        cube = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_CUBE_MAP, cube)
        for face in range(6):
            glTexImage2D(
                GL_TEXTURE_CUBE_MAP_POSITIVE_X + face, 0, GL_RGBA8, 4, 4, 0,
                GL_RGBA, GL_UNSIGNED_BYTE, None,
            )
        glFramebufferTextureFaceARB(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, cube, 0,
            GL_TEXTURE_CUBE_MAP_POSITIVE_X,
        )
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('arb geometry_shader4')

    # --- GL_ARB_imaging --------------------------------------------------
    def test_arb_imaging(self):
        self.require_extension('GL_ARB_imaging')
        from OpenGL.GL.ARB.imaging import (
            glColorTable, glColorSubTable, glCopyColorTable, glCopyColorSubTable,
            glColorTableParameterfv, glColorTableParameteriv,
            glGetColorTable, glGetColorTableParameterfv, glGetColorTableParameteriv,
            glConvolutionFilter1D, glConvolutionFilter2D, glSeparableFilter2D,
            glConvolutionParameterf, glConvolutionParameterfv,
            glConvolutionParameteri, glConvolutionParameteriv,
            glCopyConvolutionFilter1D, glCopyConvolutionFilter2D,
            glGetConvolutionFilter, glGetSeparableFilter,
            glGetConvolutionParameterfv, glGetConvolutionParameteriv,
            glHistogram, glResetHistogram, glGetHistogram,
            glGetHistogramParameterfv, glGetHistogramParameteriv,
            glMinmax, glResetMinmax, glGetMinmax,
            glGetMinmaxParameterfv, glGetMinmaxParameteriv,
            GL_COLOR_TABLE, GL_CONVOLUTION_1D, GL_CONVOLUTION_2D, GL_SEPARABLE_2D,
            GL_HISTOGRAM, GL_MINMAX, GL_CONVOLUTION_BORDER_MODE, GL_CONSTANT_BORDER,
            GL_COLOR_TABLE_SCALE, GL_HISTOGRAM_FORMAT, GL_MINMAX_FORMAT,
        )

        glBlendColor(0.0, 0.0, 0.0, 0.0)
        glBlendEquation(GL_FUNC_ADD)

        white = np.ones((4, 4), 'f')
        glColorTable(GL_COLOR_TABLE, GL_RGBA8, 4, GL_RGBA, GL_FLOAT, white)
        # A fresh 2-row array rather than white[:2]: slicing a ctypes array (the
        # no-numpy path) yields a Python list of ctypes sub-arrays that the list
        # handler cannot marshal.  Two RGBA rows of ones is the same input.
        glColorSubTable(GL_COLOR_TABLE, 0, 2, GL_RGBA, GL_FLOAT, np.ones((2, 4), 'f'))
        glColorTableParameterfv(GL_COLOR_TABLE, GL_COLOR_TABLE_SCALE, np.ones(4, 'f'))
        glColorTableParameteriv(GL_COLOR_TABLE, GL_COLOR_TABLE_SCALE, np.ones(4, 'i'))
        glGetColorTable(GL_COLOR_TABLE, GL_RGBA, GL_FLOAT)
        glGetColorTableParameterfv(GL_COLOR_TABLE, GL_COLOR_TABLE_SCALE, np.zeros(4, 'f'))
        glGetColorTableParameteriv(GL_COLOR_TABLE, GL_COLOR_TABLE_SCALE, np.zeros(4, 'i'))
        glCopyColorTable(GL_COLOR_TABLE, GL_RGBA8, 0, 0, 4)
        glCopyColorSubTable(GL_COLOR_TABLE, 0, 0, 0, 2)

        kernel = np.ones((3, 4), 'f')
        glConvolutionFilter1D(GL_CONVOLUTION_1D, GL_RGBA8, 3, GL_RGBA, GL_FLOAT, kernel)
        glConvolutionFilter2D(
            GL_CONVOLUTION_2D, GL_RGBA8, 3, 3, GL_RGBA, GL_FLOAT, np.ones((3, 3, 4), 'f')
        )
        glSeparableFilter2D(
            GL_SEPARABLE_2D, GL_RGBA8, 3, 3, GL_RGBA, GL_FLOAT, kernel, kernel
        )
        glConvolutionParameterf(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, GL_CONSTANT_BORDER)
        glConvolutionParameterfv(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, np.array([GL_CONSTANT_BORDER], 'f'))
        glConvolutionParameteri(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, GL_CONSTANT_BORDER)
        glConvolutionParameteriv(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, np.array([GL_CONSTANT_BORDER], 'i'))
        glGetConvolutionFilter(GL_CONVOLUTION_2D, GL_RGBA, GL_FLOAT)
        glGetConvolutionParameterfv(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, np.zeros(1, 'f'))
        glGetConvolutionParameteriv(GL_CONVOLUTION_2D, GL_CONVOLUTION_BORDER_MODE, np.zeros(1, 'i'))
        glGetSeparableFilter(GL_SEPARABLE_2D, GL_RGBA, GL_FLOAT)
        glCopyConvolutionFilter1D(GL_CONVOLUTION_1D, GL_RGBA8, 0, 0, 3)
        glCopyConvolutionFilter2D(GL_CONVOLUTION_2D, GL_RGBA8, 0, 0, 3, 3)

        glHistogram(GL_HISTOGRAM, 16, GL_RGBA8, GL_FALSE)
        glGetHistogram(GL_HISTOGRAM, GL_FALSE, GL_RGBA, GL_FLOAT)
        glGetHistogramParameterfv(GL_HISTOGRAM, GL_HISTOGRAM_FORMAT, np.zeros(1, 'f'))
        glGetHistogramParameteriv(GL_HISTOGRAM, GL_HISTOGRAM_FORMAT, np.zeros(1, 'i'))
        glResetHistogram(GL_HISTOGRAM)

        glMinmax(GL_MINMAX, GL_RGBA8, GL_FALSE)
        glGetMinmax(GL_MINMAX, GL_FALSE, GL_RGBA, GL_FLOAT)
        glGetMinmaxParameterfv(GL_MINMAX, GL_MINMAX_FORMAT, np.zeros(1, 'f'))
        glGetMinmaxParameteriv(GL_MINMAX, GL_MINMAX_FORMAT, np.zeros(1, 'i'))
        glResetMinmax(GL_MINMAX)
        self.check_error('arb imaging')

    # --- GL_ARB_sample_locations -----------------------------------------
    def test_arb_sample_locations(self):
        self.require_extension('GL_ARB_sample_locations')
        from OpenGL.GL.ARB.sample_locations import (
            glFramebufferSampleLocationsfvARB,
            glNamedFramebufferSampleLocationsfvARB,
            glEvaluateDepthValuesARB,
        )

        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        locations = np.array([0.5, 0.5], 'f')
        glFramebufferSampleLocationsfvARB(GL_FRAMEBUFFER, 0, 1, locations)
        glNamedFramebufferSampleLocationsfvARB(fbo, 0, 1, locations)
        glEvaluateDepthValuesARB()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('arb sample locations')

    # --- GL_ARB_sparse_buffer --------------------------------------------
    def test_arb_sparse_buffer(self):
        self.require_extension('GL_ARB_sparse_buffer')
        from OpenGL.GL.ARB.sparse_buffer import (
            glBufferPageCommitmentARB,
            glNamedBufferPageCommitmentARB,
            glNamedBufferPageCommitmentEXT,
            GL_SPARSE_STORAGE_BIT_ARB,
            GL_SPARSE_BUFFER_PAGE_SIZE_ARB,
        )

        page = int(self.getInteger(GL_SPARSE_BUFFER_PAGE_SIZE_ARB))
        size = page * 2
        for ctor in (None, 'named', 'named_ext'):
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferStorage(GL_ARRAY_BUFFER, size, None, GL_SPARSE_STORAGE_BIT_ARB)
            if ctor is None:
                glBufferPageCommitmentARB(GL_ARRAY_BUFFER, 0, page, GL_TRUE)
            elif ctor == 'named':
                glNamedBufferPageCommitmentARB(buf, 0, page, GL_TRUE)
            else:
                glNamedBufferPageCommitmentEXT(buf, 0, page, GL_TRUE)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self.check_error('arb sparse buffer')

    # --- GL_ARB_sparse_texture -------------------------------------------
    def test_arb_sparse_texture(self):
        self.require_extension('GL_ARB_sparse_texture')
        from OpenGL.GL.ARB.sparse_texture import (
            glTexPageCommitmentARB,
            GL_TEXTURE_SPARSE_ARB,
            GL_VIRTUAL_PAGE_SIZE_X_ARB,
            GL_VIRTUAL_PAGE_SIZE_Y_ARB,
        )

        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SPARSE_ARB, GL_TRUE)
        buf = np.zeros(1, 'i')
        glGetInternalformativ(GL_TEXTURE_2D, GL_RGBA8, GL_VIRTUAL_PAGE_SIZE_X_ARB, 1, buf)
        px = int(buf[0])
        glGetInternalformativ(GL_TEXTURE_2D, GL_RGBA8, GL_VIRTUAL_PAGE_SIZE_Y_ARB, 1, buf)
        py = int(buf[0])
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, px, py)
        glTexPageCommitmentARB(GL_TEXTURE_2D, 0, 0, 0, 0, px, py, 1, GL_TRUE)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.check_error('arb sparse texture')


if __name__ == '__main__':
    unittest.main()
