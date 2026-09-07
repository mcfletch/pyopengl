#! /usr/bin/env python3
"""Texture extensions: border clamp, 3D textures, clear, buffer, view,
storage, copy-image and EGL-image targets."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase
from OpenGL.GLES3 import (
    GL_TEXTURE_2D,
    GL_TEXTURE_3D,
    GL_RGBA,
    GL_RGBA8,
    GL_R32UI,
    GL_UNSIGNED_BYTE,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    glGenTextures,
    glBindTexture,
    glTexStorage2D,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    glGenFramebuffers,
    glBindFramebuffer,
)
from OpenGL.GLES2.EXT import texture_border_clamp as ext_border
from OpenGL.GLES2.OES import texture_border_clamp as oes_border
from OpenGL.GLES2.OES import texture_3D as oes_3d
from OpenGL.GLES2.EXT import clear_texture as ext_clear
from OpenGL.GLES2.EXT import texture_buffer as ext_texbuf
from OpenGL.GLES2.OES import texture_buffer as oes_texbuf
from OpenGL.GLES2.EXT import texture_view as ext_view
from OpenGL.GLES2.OES import texture_view as oes_view
from OpenGL.GLES2.EXT import texture_storage as ext_storage
from OpenGL.GLES2.EXT import copy_image as ext_copy
from OpenGL.GLES2.OES import copy_image as oes_copy
from OpenGL.GLES2.OES import texture_storage_multisample_2d_array as oes_msaa
from OpenGL.GLES2.EXT import texture_storage_compression as ext_comp
from OpenGL.GLES2.EXT.texture_border_clamp import GL_TEXTURE_BORDER_COLOR_EXT
from OpenGL.GLES2.OES.texture_border_clamp import GL_TEXTURE_BORDER_COLOR_OES
from OpenGL.GLES2.EXT.texture_buffer import GL_TEXTURE_BUFFER_EXT
from OpenGL.GLES2.OES.texture_buffer import GL_TEXTURE_BUFFER_OES
from OpenGL.GLES2.OES.texture_storage_multisample_2d_array import (
    GL_TEXTURE_2D_MULTISAMPLE_ARRAY_OES,
)
from OpenGL.GLES3 import GL_COMPRESSED_RGB8_ETC2

BORDER_I = np.array([1, 2, 3, 4], 'i')
BORDER_U = np.array([1, 2, 3, 4], 'u4')


class TestTextureExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def _tex(self, target=GL_TEXTURE_2D):
        tex = one(glGenTextures(1))
        glBindTexture(target, tex)
        return tex

    def test_ext_texture_border_clamp(self):
        self.require_extension('GL_EXT_texture_border_clamp')
        with self.exercise(
            'GL_EXT_texture_border_clamp is advertised; a driver need not serve every entry point in it'
        ):
            self._tex()
            ext_border.glTexParameterIivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_EXT, BORDER_I
            )
            ext_border.glTexParameterIuivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_EXT, BORDER_U
            )
            ext_border.glGetTexParameterIivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_EXT, np.zeros(4, 'i')
            )
            ext_border.glGetTexParameterIuivEXT(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_EXT, np.zeros(4, 'u4')
            )
            from OpenGL.GLES3 import glGenSamplers

            s = one(glGenSamplers(1))
            ext_border.glSamplerParameterIivEXT(
                s, GL_TEXTURE_BORDER_COLOR_EXT, BORDER_I
            )
            ext_border.glSamplerParameterIuivEXT(
                s, GL_TEXTURE_BORDER_COLOR_EXT, BORDER_U
            )
            ext_border.glGetSamplerParameterIivEXT(
                s, GL_TEXTURE_BORDER_COLOR_EXT, np.zeros(4, 'i')
            )
            ext_border.glGetSamplerParameterIuivEXT(
                s, GL_TEXTURE_BORDER_COLOR_EXT, np.zeros(4, 'u4')
            )
            self.check_error('ext border clamp')

    def test_oes_texture_border_clamp(self):
        self.require_extension('GL_OES_texture_border_clamp')
        with self.exercise(
            'GL_OES_texture_border_clamp is advertised; a driver need not serve every entry point in it'
        ):
            self._tex()
            oes_border.glTexParameterIivOES(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_OES, BORDER_I
            )
            oes_border.glTexParameterIuivOES(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_OES, BORDER_U
            )
            oes_border.glGetTexParameterIivOES(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_OES, np.zeros(4, 'i')
            )
            oes_border.glGetTexParameterIuivOES(
                GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR_OES, np.zeros(4, 'u4')
            )
            from OpenGL.GLES3 import glGenSamplers

            s = one(glGenSamplers(1))
            oes_border.glSamplerParameterIivOES(
                s, GL_TEXTURE_BORDER_COLOR_OES, BORDER_I
            )
            oes_border.glSamplerParameterIuivOES(
                s, GL_TEXTURE_BORDER_COLOR_OES, BORDER_U
            )
            oes_border.glGetSamplerParameterIivOES(
                s, GL_TEXTURE_BORDER_COLOR_OES, np.zeros(4, 'i')
            )
            oes_border.glGetSamplerParameterIuivOES(
                s, GL_TEXTURE_BORDER_COLOR_OES, np.zeros(4, 'u4')
            )
            self.check_error('oes border clamp')

    def test_oes_texture_3d(self):
        self.require_extension('GL_OES_texture_3D')
        with self.exercise(
            'GL_OES_texture_3D is advertised; a driver need not serve every entry point in it'
        ):
            self._tex(GL_TEXTURE_3D)
            vol = np.zeros((2, 2, 2, 4), np.uint8)
            oes_3d.glTexImage3DOES(
                GL_TEXTURE_3D, 0, GL_RGBA, 2, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, vol
            )
            oes_3d.glTexSubImage3DOES(
                GL_TEXTURE_3D, 0, 0, 0, 0, 2, 2, 2, GL_RGBA, GL_UNSIGNED_BYTE, vol
            )
            oes_3d.glCopyTexSubImage3DOES(GL_TEXTURE_3D, 0, 0, 0, 0, 0, 0, 2, 2)
            oes_3d.glCompressedTexImage3DOES(
                GL_TEXTURE_3D,
                0,
                GL_COMPRESSED_RGB8_ETC2,
                4,
                4,
                1,
                0,
                8,
                np.zeros(8, 'u1'),
            )
            oes_3d.glCompressedTexSubImage3DOES(
                GL_TEXTURE_3D,
                0,
                0,
                0,
                0,
                4,
                4,
                1,
                GL_COMPRESSED_RGB8_ETC2,
                8,
                np.zeros(8, 'u1'),
            )
            fbo = one(glGenFramebuffers(1))
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            oes_3d.glFramebufferTexture3DOES(
                GL_FRAMEBUFFER,
                GL_COLOR_ATTACHMENT0,
                GL_TEXTURE_3D,
                self._tex(GL_TEXTURE_3D),
                0,
                0,
            )
            self.check_error('oes texture 3d')

    def test_ext_clear_texture(self):
        self.require_extension('GL_EXT_clear_texture')
        with self.exercise(
            'GL_EXT_clear_texture is advertised; a driver need not serve every entry point in it'
        ):
            tex = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            ext_clear.glClearTexImageEXT(
                tex, 0, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros(4, 'u1')
            )
            ext_clear.glClearTexSubImageEXT(
                tex, 0, 0, 0, 0, 2, 2, 1, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros(4, 'u1')
            )
            self.check_error('clear texture')

    def test_ext_texture_buffer(self):
        self.require_extension('GL_EXT_texture_buffer')
        with self.exercise(
            'GL_EXT_texture_buffer is advertised; a driver need not serve every entry point in it'
        ):
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'u4'), GL_STATIC_DRAW)
            self._tex(GL_TEXTURE_BUFFER_EXT)
            ext_texbuf.glTexBufferEXT(GL_TEXTURE_BUFFER_EXT, GL_R32UI, buf)
            ext_texbuf.glTexBufferRangeEXT(GL_TEXTURE_BUFFER_EXT, GL_R32UI, buf, 0, 64)
            self.check_error('ext texture buffer')

    def test_oes_texture_buffer(self):
        self.require_extension('GL_OES_texture_buffer')
        with self.exercise(
            'GL_OES_texture_buffer is advertised; a driver need not serve every entry point in it'
        ):
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'u4'), GL_STATIC_DRAW)
            self._tex(GL_TEXTURE_BUFFER_OES)
            oes_texbuf.glTexBufferOES(GL_TEXTURE_BUFFER_OES, GL_R32UI, buf)
            oes_texbuf.glTexBufferRangeOES(GL_TEXTURE_BUFFER_OES, GL_R32UI, buf, 0, 64)
            self.check_error('oes texture buffer')

    def test_texture_view(self):
        self.require_extension('GL_EXT_texture_view')
        with self.exercise(
            'GL_EXT_texture_view is advertised; a driver need not serve every entry point in it'
        ):
            orig = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            view = one(glGenTextures(1))
            ext_view.glTextureViewEXT(view, GL_TEXTURE_2D, orig, GL_RGBA8, 0, 1, 0, 1)
            self.check_error('ext texture view')

    def test_oes_texture_view(self):
        self.require_extension('GL_OES_texture_view')
        with self.exercise(
            'GL_OES_texture_view is advertised; a driver need not serve every entry point in it'
        ):
            orig = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            view = one(glGenTextures(1))
            oes_view.glTextureViewOES(view, GL_TEXTURE_2D, orig, GL_RGBA8, 0, 1, 0, 1)
            self.check_error('oes texture view')

    def test_ext_texture_storage(self):
        self.require_extension('GL_EXT_texture_storage')
        with self.exercise(
            'GL_EXT_texture_storage is advertised; a driver need not serve every entry point in it'
        ):
            self._tex()
            ext_storage.glTexStorage2DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
            self._tex(GL_TEXTURE_3D)
            ext_storage.glTexStorage3DEXT(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4)
            self._tex()
            # 1D targets and the DSA forms are unsupported in ES, so these fail GL
            # validation; the calls still drive the wrappers -- exercise() tolerates
            ext_storage.glTexStorage1DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4)
            ext_storage.glTextureStorage1DEXT(
                one(glGenTextures(1)), GL_TEXTURE_2D, 1, GL_RGBA8, 4
            )
            ext_storage.glTextureStorage2DEXT(
                one(glGenTextures(1)), GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4
            )
            ext_storage.glTextureStorage3DEXT(
                one(glGenTextures(1)), GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4
            )
            self.check_error('ext texture storage')

    def test_copy_image(self):
        self.require_extension('GL_EXT_copy_image')
        with self.exercise(
            'GL_EXT_copy_image is advertised; a driver need not serve every entry point in it'
        ):
            a = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
            b = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
            ext_copy.glCopyImageSubDataEXT(
                a, GL_TEXTURE_2D, 0, 0, 0, 0, b, GL_TEXTURE_2D, 0, 0, 0, 0, 8, 8, 1
            )
            self.check_error('ext copy image')

    def test_oes_copy_image(self):
        self.require_extension('GL_OES_copy_image')
        with self.exercise(
            'GL_OES_copy_image is advertised; a driver need not serve every entry point in it'
        ):
            a = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
            b = self._tex()
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
            oes_copy.glCopyImageSubDataOES(
                a, GL_TEXTURE_2D, 0, 0, 0, 0, b, GL_TEXTURE_2D, 0, 0, 0, 0, 8, 8, 1
            )
            self.check_error('oes copy image')

    def test_oes_msaa_array_storage(self):
        self.require_extension('GL_OES_texture_storage_multisample_2d_array')
        with self.exercise(
            'GL_OES_texture_storage_multisample_2d_array is advertised; a driver need not serve every entry point in it'
        ):
            self._tex(GL_TEXTURE_2D_MULTISAMPLE_ARRAY_OES)
            oes_msaa.glTexStorage3DMultisampleOES(
                GL_TEXTURE_2D_MULTISAMPLE_ARRAY_OES, 4, GL_RGBA8, 8, 8, 2, True
            )
            self.check_error('oes msaa array storage')

    def test_ext_texture_storage_compression(self):
        self.require_extension('GL_EXT_texture_storage_compression')
        with self.exercise(
            'GL_EXT_texture_storage_compression is advertised; a driver need not serve every entry point in it'
        ):
            self._tex()
            ext_comp.glTexStorageAttribs2DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4, None)
            self._tex(GL_TEXTURE_3D)
            ext_comp.glTexStorageAttribs3DEXT(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4, None)
            self.check_error('storage compression')


if __name__ == '__main__':
    unittest.main()
