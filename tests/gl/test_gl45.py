#! /usr/bin/env python3
"""GL 4.5 (compatibility): direct state access, robustness queries, clip control."""

import unittest
import ctypes
from arraycompat import nbytes, np, object_names, one

from arraycompat import copy_safe
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


def _one(x):
    return int(x[0]) if hasattr(x, '__len__') else int(x)


def _create(fn, *prefix):
    """DSA glCreate* need an explicit (n, out) output array (no auto-alloc)."""
    out = np.zeros(1, 'I')
    fn(*(prefix + (1, out)))
    return int(out[0])


class TestGL45(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def test_dsa_buffers(self):
        buf = _create(glCreateBuffers)
        glNamedBufferStorage(
            buf, 64, None, GL_DYNAMIC_STORAGE_BIT | GL_MAP_READ_BIT | GL_MAP_WRITE_BIT
        )
        glNamedBufferSubData(buf, 0, 16, np.ones(4, 'f'))
        buf2 = _create(glCreateBuffers)
        glNamedBufferData(buf2, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glCopyNamedBufferSubData(buf, buf2, 0, 0, 16)
        glClearNamedBufferData(buf2, GL_R32F, GL_RED, GL_FLOAT, None)
        glClearNamedBufferSubData(buf2, GL_R32F, 0, 16, GL_RED, GL_FLOAT, None)
        glMapNamedBuffer(buf, GL_READ_ONLY)
        glUnmapNamedBuffer(buf)
        glMapNamedBufferRange(buf, 0, 16, GL_MAP_WRITE_BIT | GL_MAP_FLUSH_EXPLICIT_BIT)
        glFlushMappedNamedBufferRange(buf, 0, 16)
        glUnmapNamedBuffer(buf)
        glGetNamedBufferParameteriv(buf, GL_BUFFER_SIZE, np.zeros(1, 'i'))
        glGetNamedBufferParameteri64v(buf, GL_BUFFER_SIZE, np.zeros(1, 'q'))
        glGetNamedBufferPointerv(
            buf, GL_BUFFER_MAP_POINTER, ctypes.byref(ctypes.c_void_p())
        )
        glGetNamedBufferSubData(buf, 0, 16, (ctypes.c_ubyte * 16)())
        self.check_error('dsa buffers')

    def test_dsa_textures(self):
        tex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(tex, 1, GL_RGBA8, 16, 16)
        glTextureSubImage2D(
            tex, 0, 0, 0, 4, 4, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros((4, 4, 4), 'B')
        )
        glTextureParameteri(tex, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTextureParameterf(tex, GL_TEXTURE_MAX_LOD, 1.0)
        glTextureParameteriv(tex, GL_TEXTURE_WRAP_S, np.array([GL_CLAMP_TO_EDGE], 'i'))
        glTextureParameterfv(tex, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'f'))
        glTextureParameterIiv(tex, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i'))
        glTextureParameterIuiv(tex, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I'))
        glGetTextureParameteriv(tex, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'i'))
        glGetTextureParameterfv(tex, GL_TEXTURE_MAX_LOD, np.zeros(1, 'f'))
        glGetTextureParameterIiv(tex, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i'))
        glGetTextureParameterIuiv(tex, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I'))
        glGetTextureLevelParameteriv(tex, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'i'))
        glGetTextureLevelParameterfv(tex, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'f'))
        glGenerateTextureMipmap(tex)
        glGetTextureImage(
            tex,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            16 * 16 * 4,
            (ctypes.c_ubyte * (16 * 16 * 4))(),
        )
        glGetTextureSubImage(
            tex,
            0,
            0,
            0,
            0,
            4,
            4,
            1,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            4 * 4 * 4,
            (ctypes.c_ubyte * (4 * 4 * 4))(),
        )
        glCopyTextureSubImage2D(tex, 0, 0, 0, 0, 0, 4, 4)
        glBindTextureUnit(0, tex)
        tex1 = _create(glCreateTextures, GL_TEXTURE_1D)
        glTextureStorage1D(tex1, 1, GL_RGBA8, 16)
        glTextureSubImage1D(
            tex1, 0, 0, 4, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros((4, 4), 'B')
        )
        glCopyTextureSubImage1D(tex1, 0, 0, 0, 0, 4)
        tex3 = _create(glCreateTextures, GL_TEXTURE_3D)
        glTextureStorage3D(tex3, 1, GL_RGBA8, 4, 4, 4)
        glTextureSubImage3D(
            tex3,
            0,
            0,
            0,
            0,
            4,
            4,
            4,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((4, 4, 4, 4), 'B'),
        )
        glCopyTextureSubImage3D(tex3, 0, 0, 0, 0, 0, 0, 4, 4)
        msa = _create(glCreateTextures, GL_TEXTURE_2D_MULTISAMPLE)
        glTextureStorage2DMultisample(msa, 4, GL_RGBA8, 16, 16, GL_TRUE)
        ma = _create(glCreateTextures, GL_TEXTURE_2D_MULTISAMPLE_ARRAY)
        glTextureStorage3DMultisample(ma, 4, GL_RGBA8, 16, 16, 2, GL_TRUE)
        tbuf = _create(glCreateBuffers)
        glNamedBufferData(tbuf, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
        tbtex = _create(glCreateTextures, GL_TEXTURE_BUFFER)
        glTextureBuffer(tbtex, GL_R32F, tbuf)
        glTextureBufferRange(tbtex, GL_R32F, tbuf, 0, 16)
        block = np.zeros(8, 'B')  # one ETC2 4x4 RGB block
        ctex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(ctex, 1, GL_COMPRESSED_RGB8_ETC2, 4, 4)
        glCompressedTextureSubImage2D(
            ctex, 0, 0, 0, 4, 4, GL_COMPRESSED_RGB8_ETC2, nbytes(block), block
        )
        glGetCompressedTextureImage(ctex, 0, nbytes(block), np.zeros(8, 'B'))
        glGetCompressedTextureSubImage(
            ctex, 0, 0, 0, 0, 4, 4, 1, nbytes(block), np.zeros(8, 'B')
        )
        with self.exercise():  # 1D/3D compressed targets are format-restricted
            c1 = _create(glCreateTextures, GL_TEXTURE_1D)
            glCompressedTextureSubImage1D(
                c1, 0, 0, 4, GL_COMPRESSED_RGB8_ETC2, nbytes(block), block
            )
            c3 = _create(glCreateTextures, GL_TEXTURE_3D)
            glCompressedTextureSubImage3D(
                c3, 0, 0, 0, 0, 4, 4, 1, GL_COMPRESSED_RGB8_ETC2, nbytes(block), block
            )
        self.check_error('dsa textures')

    def test_dsa_framebuffers_renderbuffers(self):
        tex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(tex, 1, GL_RGBA8, 16, 16)
        fbo = _create(glCreateFramebuffers)
        glNamedFramebufferTexture(fbo, GL_COLOR_ATTACHMENT0, tex, 0)
        glNamedFramebufferDrawBuffer(fbo, GL_COLOR_ATTACHMENT0)
        glNamedFramebufferDrawBuffers(fbo, 1, object_names(GL_COLOR_ATTACHMENT0))
        glNamedFramebufferReadBuffer(fbo, GL_COLOR_ATTACHMENT0)
        self.assertEqual(
            glCheckNamedFramebufferStatus(fbo, GL_FRAMEBUFFER), GL_FRAMEBUFFER_COMPLETE
        )
        glClearNamedFramebufferfv(fbo, GL_COLOR, 0, np.array([0, 0, 0, 1], 'f'))
        glGetNamedFramebufferAttachmentParameteriv(
            fbo,
            GL_COLOR_ATTACHMENT0,
            GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE,
            np.zeros(1, 'i'),
        )
        glGetNamedFramebufferParameteriv(fbo, GL_SAMPLES, np.zeros(1, 'i'))
        # no-attachment framebuffer for default-geometry parameters
        empty = _create(glCreateFramebuffers)
        glNamedFramebufferParameteri(empty, GL_FRAMEBUFFER_DEFAULT_WIDTH, 16)
        glNamedFramebufferParameteri(empty, GL_FRAMEBUFFER_DEFAULT_HEIGHT, 16)
        # integer/unsigned/depth-stencil clears need correctly-typed attachments
        itex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(itex, 1, GL_RGBA32I, 4, 4)
        ifbo = _create(glCreateFramebuffers)
        glNamedFramebufferTexture(ifbo, GL_COLOR_ATTACHMENT0, itex, 0)
        glClearNamedFramebufferiv(ifbo, GL_COLOR, 0, np.zeros(4, 'i'))
        utex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(utex, 1, GL_RGBA32UI, 4, 4)
        ufbo = _create(glCreateFramebuffers)
        glNamedFramebufferTexture(ufbo, GL_COLOR_ATTACHMENT0, utex, 0)
        glClearNamedFramebufferuiv(ufbo, GL_COLOR, 0, np.zeros(4, 'I'))
        dstex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(dstex, 1, GL_DEPTH24_STENCIL8, 4, 4)
        dfbo = _create(glCreateFramebuffers)
        glNamedFramebufferTexture(dfbo, GL_DEPTH_STENCIL_ATTACHMENT, dstex, 0)
        glClearNamedFramebufferfi(dfbo, GL_DEPTH_STENCIL, 0, 1.0, 0)
        rb = _create(glCreateRenderbuffers)
        glNamedRenderbufferStorage(rb, GL_RGBA8, 16, 16)
        glNamedRenderbufferStorageMultisample(rb, 4, GL_RGBA8, 16, 16)
        drb = _create(glCreateRenderbuffers)
        glNamedRenderbufferStorage(drb, GL_DEPTH_COMPONENT24, 16, 16)
        glNamedFramebufferRenderbuffer(fbo, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, drb)
        glGetNamedRenderbufferParameteriv(rb, GL_RENDERBUFFER_WIDTH, np.zeros(1, 'i'))
        fbo2 = _create(glCreateFramebuffers)
        tex2 = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(tex2, 1, GL_RGBA8, 16, 16)
        glNamedFramebufferTexture(fbo2, GL_COLOR_ATTACHMENT0, tex2, 0)
        glBlitNamedFramebuffer(
            fbo, fbo2, 0, 0, 16, 16, 0, 0, 16, 16, GL_COLOR_BUFFER_BIT, GL_NEAREST
        )
        glInvalidateNamedFramebufferData(fbo, 1, copy_safe([GL_COLOR_ATTACHMENT0], 'I'))
        glInvalidateNamedFramebufferSubData(
            fbo, 1, copy_safe([GL_COLOR_ATTACHMENT0], 'I'), 0, 0, 8, 8
        )
        arrtex = _create(glCreateTextures, GL_TEXTURE_2D_ARRAY)
        glTextureStorage3D(arrtex, 1, GL_RGBA8, 16, 16, 2)
        glNamedFramebufferTextureLayer(fbo, GL_COLOR_ATTACHMENT0, arrtex, 0, 1)
        self.check_error('dsa framebuffers')

    def test_dsa_vertex_arrays(self):
        vao = _create(glCreateVertexArrays)
        buf = _create(glCreateBuffers)
        glNamedBufferData(buf, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
        ebo = _create(glCreateBuffers)
        glNamedBufferData(ebo, 16, np.zeros(4, 'I'), GL_STATIC_DRAW)
        glVertexArrayVertexBuffer(vao, 0, buf, 0, 16)
        glVertexArrayVertexBuffers(
            vao,
            0,
            1,
            np.array([buf], 'I'),
            (ctypes.c_ssize_t * 1)(0),
            (ctypes.c_int * 1)(16),
        )
        glVertexArrayElementBuffer(vao, ebo)
        glVertexArrayAttribFormat(vao, 0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexArrayAttribIFormat(vao, 1, 4, GL_INT, 0)
        glVertexArrayAttribLFormat(vao, 2, 4, GL_DOUBLE, 0)
        glVertexArrayAttribBinding(vao, 0, 0)
        glVertexArrayBindingDivisor(vao, 0, 1)
        glEnableVertexArrayAttrib(vao, 0)
        glDisableVertexArrayAttrib(vao, 0)
        glGetVertexArrayiv(vao, GL_ELEMENT_ARRAY_BUFFER_BINDING, np.zeros(1, 'i'))
        glGetVertexArrayIndexediv(
            vao, 0, GL_VERTEX_ATTRIB_ARRAY_ENABLED, np.zeros(1, 'i')
        )
        glGetVertexArrayIndexed64iv(vao, 0, GL_VERTEX_BINDING_OFFSET, np.zeros(1, 'q'))
        self.check_error('dsa vertex arrays')

    def test_dsa_xfb_queries_samplers(self):
        tfo = _create(glCreateTransformFeedbacks)
        buf = _create(glCreateBuffers)
        glNamedBufferData(buf, 64, np.zeros(16, 'f'), GL_DYNAMIC_COPY)
        glTransformFeedbackBufferBase(tfo, 0, buf)
        glTransformFeedbackBufferRange(tfo, 0, buf, 0, 16)
        glGetTransformFeedbackiv(tfo, GL_TRANSFORM_FEEDBACK_ACTIVE, np.zeros(1, 'i'))
        glGetTransformFeedbacki_v(
            tfo, GL_TRANSFORM_FEEDBACK_BUFFER_BINDING, 0, np.zeros(1, 'i')
        )
        glGetTransformFeedbacki64_v(
            tfo, GL_TRANSFORM_FEEDBACK_BUFFER_START, 0, np.zeros(1, 'q')
        )
        q = _create(glCreateQueries, GL_SAMPLES_PASSED)
        glBeginQuery(GL_SAMPLES_PASSED, q)
        glEndQuery(GL_SAMPLES_PASSED)
        qbuf = _create(glCreateBuffers)
        glNamedBufferData(qbuf, 32, np.zeros(8, 'I'), GL_DYNAMIC_READ)
        glBindBuffer(GL_QUERY_BUFFER, qbuf)
        glGetQueryBufferObjectiv(q, qbuf, GL_QUERY_RESULT, 0)
        glGetQueryBufferObjectuiv(q, qbuf, GL_QUERY_RESULT, 8)
        glGetQueryBufferObjecti64v(q, qbuf, GL_QUERY_RESULT, 16)
        glGetQueryBufferObjectui64v(q, qbuf, GL_QUERY_RESULT, 24)
        glBindBuffer(GL_QUERY_BUFFER, 0)
        _create(glCreateSamplers)
        _create(glCreateProgramPipelines)
        self.check_error('dsa xfb/queries/samplers')

    def test_robustness_and_misc(self):
        glClipControl(GL_LOWER_LEFT, GL_ZERO_TO_ONE)
        glTextureBarrier()
        glMemoryBarrierByRegion(GL_ALL_BARRIER_BITS)
        self.assertEqual(one(glGetGraphicsResetStatus()), int(GL_NO_ERROR))
        size = self.width * self.height * 4
        glReadnPixels(
            0,
            0,
            self.width,
            self.height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            size,
            (ctypes.c_ubyte * size)(),
        )
        tex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(tex, 1, GL_RGBA8, 4, 4)
        glBindTexture(GL_TEXTURE_2D, tex)
        self.require_entrypoint(glGetnTexImage, 'glGetnTexImage')
        glGetnTexImage(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            4 * 4 * 4,
            (ctypes.c_ubyte * (4 * 4 * 4))(),
        )
        program = self.compile_program(
            '#version 450 compatibility\nuniform vec4 u; void main(){gl_Position=gl_Vertex; gl_FrontColor=u;}',
            '#version 450 compatibility\nvoid main(){gl_FragColor=gl_Color;}',
        )
        glUseProgram(program)
        loc = glGetUniformLocation(program, 'u')
        glGetnUniformfv(program, loc, 16, np.zeros(4, 'f'))
        glGetnUniformiv(program, loc, 16, np.zeros(4, 'i'))
        glGetnUniformuiv(program, loc, 16, np.zeros(4, 'I'))
        glGetnUniformdv(program, loc, 32, np.zeros(4, 'd'))
        self.check_error('robustness/misc')

    def test_legacy_robustness(self):
        self.require_entrypoint(glGetnPolygonStipple, 'glGetnPolygonStipple')
        glGetnPolygonStipple(128, np.zeros(128, 'B'))
        # NVIDIA advertises KHR_robustness but does not actually serve these
        # robust legacy getters -- the non-robust glGetPixelMap*/glGetMap*
        # succeed in the same context, so the args/state are valid; tolerate the
        # driver's INVALID_OPERATION while still exercising each entry point.
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnPixelMapfv(GL_PIXEL_MAP_R_TO_R, 2, np.zeros(2, 'f'))
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnPixelMapuiv(GL_PIXEL_MAP_I_TO_I, 2, np.zeros(2, 'I'))
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnPixelMapusv(GL_PIXEL_MAP_S_TO_S, 2, np.zeros(2, 'H'))
        glMap1f(GL_MAP1_VERTEX_3, 0, 1, np.array([[0, 0, 0], [1, 1, 0]], 'f'))
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnMapfv(GL_MAP1_VERTEX_3, GL_COEFF, 6, np.zeros(6, 'f'))
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnMapdv(GL_MAP1_VERTEX_3, GL_COEFF, 6, np.zeros(6, 'd'))
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glGetnMapiv(GL_MAP1_VERTEX_3, GL_ORDER, 1, np.zeros(1, 'i'))
        ctex = _create(glCreateTextures, GL_TEXTURE_2D)
        glTextureStorage2D(ctex, 1, GL_COMPRESSED_RGB8_ETC2, 4, 4)
        glBindTexture(GL_TEXTURE_2D, ctex)
        glGetnCompressedTexImage(GL_TEXTURE_2D, 0, 8, np.zeros(8, 'B'))
        self.check_error('legacy robustness')

    def test_legacy_imaging_robustness(self):
        self.require_extension('GL_ARB_imaging')
        # the imaging getters need histogram/minmax/table state; exercise()
        # runs the wrapper and tolerates the resulting state GLErrors
        with self.exercise():
            glGetnColorTable(
                GL_COLOR_TABLE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnConvolutionFilter(
                GL_CONVOLUTION_2D, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnSeparableFilter(
                GL_SEPARABLE_2D,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                16,
                np.zeros(16, 'B'),
                16,
                np.zeros(16, 'B'),
                None,
            )
            glGetnHistogram(
                GL_HISTOGRAM, GL_TRUE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnMinmax(
                GL_MINMAX, GL_TRUE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )


if __name__ == '__main__':
    unittest.main()
