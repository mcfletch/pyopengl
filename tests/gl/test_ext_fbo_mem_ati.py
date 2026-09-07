#! /usr/bin/env python3
"""GL_EXT_framebuffer_object (pre-core FBOs), the EXT framebuffer aliases of
core blit/multisample/layered-attachment, GL_EXT_memory_object (+ _fd external
import) and GL_ATI_fragment_shader (legacy register combiners)."""

import unittest

from OpenGL import acceleratesupport
from arraycompat import np, object_names

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.EXT.framebuffer_object import *  # noqa: F401,F403
from OpenGL.GL.EXT.framebuffer_blit import *  # noqa: F401,F403
from OpenGL.GL.EXT.framebuffer_multisample import *  # noqa: F401,F403
from OpenGL.GL.EXT.texture_array import *  # noqa: F401,F403
from OpenGL.GL.EXT.memory_object import *  # noqa: F401,F403
from OpenGL.GL.EXT.memory_object_fd import *  # noqa: F401,F403
from OpenGL.GL.ATI.fragment_shader import *  # noqa: F401,F403


class TestEXTFramebufferObject(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_framebuffer_object(self):
        self.require_extension('GL_EXT_framebuffer_object')
        with self.allow_missing():
            fbo = int(glGenFramebuffersEXT(1))
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)
            self.assertTrue(glIsFramebufferEXT(fbo))
            rbo = int(glGenRenderbuffersEXT(1))
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, rbo)
            self.assertTrue(glIsRenderbufferEXT(rbo))
            glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, GL_RGBA8, 16, 16)
            glGetRenderbufferParameterivEXT(
                GL_RENDERBUFFER_EXT, GL_RENDERBUFFER_WIDTH_EXT, np.zeros(1, 'i')
            )
            glFramebufferRenderbufferEXT(
                GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_RENDERBUFFER_EXT, rbo
            )
            tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA8, 16, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            glFramebufferTexture2DEXT(
                GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_2D, tex, 0
            )
            glGetFramebufferAttachmentParameterivEXT(
                GL_FRAMEBUFFER_EXT,
                GL_COLOR_ATTACHMENT0_EXT,
                GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE_EXT,
                np.zeros(1, 'i'),
            )
            glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)
            glGenerateMipmapEXT(GL_TEXTURE_2D)
            t1 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_1D, t1)
            glTexImage1D(
                GL_TEXTURE_1D, 0, GL_RGBA8, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
            )
            f1 = int(glGenFramebuffersEXT(1))
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, f1)
            glFramebufferTexture1DEXT(
                GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_1D, t1, 0
            )
            t3 = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_3D, t3)
            glTexImage3D(
                GL_TEXTURE_3D,
                0,
                GL_RGBA8,
                16,
                16,
                2,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                None,
            )
            f3 = int(glGenFramebuffersEXT(1))
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, f3)
            glFramebufferTexture3DEXT(
                GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_3D, t3, 0, 0
            )
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
            glDeleteFramebuffersEXT(1, object_names(fbo))
            glDeleteRenderbuffersEXT(1, object_names(rbo))
        self.check_error('EXT framebuffer object')


class TestEXTFramebufferAliases(GLTestCase):
    """EXT-suffixed aliases of core framebuffer entry points: the blit,
    multisample renderbuffer storage and layered (texture-array) attachment
    that predate their promotion into GL 3.0."""

    profile = 'core'
    gl_version = (4, 5)

    def test_framebuffer_blit(self):
        self.require_extension('GL_EXT_framebuffer_blit')
        src = int(glGenFramebuffers(1))
        dst = int(glGenFramebuffers(1))
        for fbo in (src, dst):
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            rb = int(glGenRenderbuffers(1))
            glBindRenderbuffer(GL_RENDERBUFFER, rb)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, 16, 16)
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rb
            )
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst)
        with self.exercise():
            glBlitFramebufferEXT(
                0, 0, 16, 16, 0, 0, 16, 16, GL_COLOR_BUFFER_BIT, GL_NEAREST
            )

    def test_framebuffer_multisample(self):
        self.require_extension('GL_EXT_framebuffer_multisample')
        rb = int(glGenRenderbuffers(1))
        glBindRenderbuffer(GL_RENDERBUFFER, rb)
        with self.exercise():
            glRenderbufferStorageMultisampleEXT(GL_RENDERBUFFER, 4, GL_RGBA8, 16, 16)

    def test_texture_array_layer_attach(self):
        self.require_extension('GL_EXT_texture_array')
        arr = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_ARRAY, arr)
        glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 16, 16, 2)
        fbo = int(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        with self.exercise():
            glFramebufferTextureLayerEXT(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, arr, 0, 0
            )


class TestEXTMemoryObject(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_memory_object(self):
        self.require_extension('GL_EXT_memory_object')
        with self.allow_missing():
            n = self.getInteger(GL_NUM_DEVICE_UUIDS_EXT)
            glGetUnsignedBytevEXT(GL_DRIVER_UUID_EXT, np.zeros(16, 'B'))
            if n > 0:
                glGetUnsignedBytei_vEXT(GL_DEVICE_UUID_EXT, 0, np.zeros(16, 'B'))
            mids = np.zeros(1, 'I')
            glCreateMemoryObjectsEXT(1, mids)
            mem = int(mids[0])
            self.assertTrue(glIsMemoryObjectEXT(mem))
            glMemoryObjectParameterivEXT(
                mem, GL_DEDICATED_MEMORY_OBJECT_EXT, np.array([GL_FALSE], 'i')
            )
            glGetMemoryObjectParameterivEXT(
                mem, GL_DEDICATED_MEMORY_OBJECT_EXT, np.zeros(1, 'i')
            )
            glDeleteMemoryObjectsEXT(1, object_names(mem))
        # storage-from-memory needs an imported allocation we cannot make here,
        # so the calls fail GL validation -- but they still drive the wrapper's
        # argument marshalling, which is what we are testing; exercise() tolerates
        with self.exercise():
            mids2 = np.zeros(1, 'I')
            glCreateMemoryObjectsEXT(1, mids2)
            m2 = int(mids2[0])
            buf = int(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferStorageMemEXT(GL_ARRAY_BUFFER, 64, m2, 0)
            glNamedBufferStorageMemEXT(int(glGenBuffers(1)), 64, m2, 0)
            glBindTexture(GL_TEXTURE_1D, int(glGenTextures(1)))
            glTexStorageMem1DEXT(GL_TEXTURE_1D, 1, GL_RGBA8, 4, m2, 0)
            glBindTexture(GL_TEXTURE_2D, int(glGenTextures(1)))
            glTexStorageMem2DEXT(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4, m2, 0)
            glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, int(glGenTextures(1)))
            glTexStorageMem2DMultisampleEXT(
                GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 4, 4, GL_TRUE, m2, 0
            )
            glBindTexture(GL_TEXTURE_3D, int(glGenTextures(1)))
            glTexStorageMem3DEXT(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4, m2, 0)
            glBindTexture(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, int(glGenTextures(1)))
            glTexStorageMem3DMultisampleEXT(
                GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 4, 4, 2, GL_TRUE, m2, 0
            )
            glTextureStorageMem1DEXT(int(glGenTextures(1)), 1, GL_RGBA8, 4, m2, 0)
            glTextureStorageMem2DEXT(int(glGenTextures(1)), 1, GL_RGBA8, 4, 4, m2, 0)
            glTextureStorageMem2DMultisampleEXT(
                int(glGenTextures(1)), 4, GL_RGBA8, 4, 4, GL_TRUE, m2, 0
            )
            glTextureStorageMem3DEXT(int(glGenTextures(1)), 1, GL_RGBA8, 4, 4, 4, m2, 0)
            glTextureStorageMem3DMultisampleEXT(
                int(glGenTextures(1)), 4, GL_RGBA8, 4, 4, 2, GL_TRUE, m2, 0
            )

    def test_memory_object_fd(self):
        self.require_extension('GL_EXT_memory_object_fd')
        # No opaque-fd handle is available headless; fd=-1 is rejected with a
        # GLError, which exercise() tolerates -- the wrapper still runs.
        with self.exercise():
            mids = np.zeros(1, 'I')
            glCreateMemoryObjectsEXT(1, mids)
            glImportMemoryFdEXT(
                int(mids[0]), 1024, GL_HANDLE_TYPE_OPAQUE_FD_EXT, -1
            )


class TestATIFragmentShader(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_ati_fragment_shader(self):
        self.require_extension('GL_ATI_fragment_shader')
        with self.allow_missing():
            sid = glGenFragmentShadersATI(1)
            glBindFragmentShaderATI(sid)
            glBeginFragmentShaderATI()
            glPassTexCoordATI(GL_REG_0_ATI, GL_TEXTURE0, GL_SWIZZLE_STR_ATI)
            glSampleMapATI(GL_REG_1_ATI, GL_TEXTURE0, GL_SWIZZLE_STR_ATI)
            glColorFragmentOp1ATI(
                GL_MOV_ATI,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
            )
            glColorFragmentOp2ATI(
                GL_ADD_ATI,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_1_ATI,
                GL_NONE,
                GL_NONE,
            )
            glColorFragmentOp3ATI(
                GL_MAD_ATI,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_1_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
            )
            glAlphaFragmentOp1ATI(
                GL_MOV_ATI, GL_REG_0_ATI, GL_NONE, GL_REG_0_ATI, GL_NONE, GL_NONE
            )
            glAlphaFragmentOp2ATI(
                GL_ADD_ATI,
                GL_REG_0_ATI,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_1_ATI,
                GL_NONE,
                GL_NONE,
            )
            glAlphaFragmentOp3ATI(
                GL_MAD_ATI,
                GL_REG_0_ATI,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_1_ATI,
                GL_NONE,
                GL_NONE,
                GL_REG_0_ATI,
                GL_NONE,
                GL_NONE,
            )
            glEndFragmentShaderATI()
            glSetFragmentShaderConstantATI(GL_CON_0_ATI, np.zeros(4, 'f'))
            glDeleteFragmentShaderATI(sid)
        self.check_error('ATI fragment shader')


class TestAttachingATextureToAnEXTFramebuffer(GLTestCase):
    """SF#2946228: attaching a texture used to raise where nothing was wrong.

    ``glFramebufferTexture2DEXT`` raised spuriously with the C accelerator
    switched off, so the configuration this is about is the one without it.
    Whether the accelerator is in use is decided when the wrappers are built
    and cannot be changed from here, so this asks rather than sets: run with
    ``PYOPENGL_USE_ACCELERATE=0``, which ``OpenGL/__init__.py`` reads before
    anything consults it, or on a tox ``accel0`` axis, where it is not
    installed at all.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    @unittest.skipIf(
        acceleratesupport.ACCELERATE_AVAILABLE,
        'the defect was in the path without the C accelerator; run with '
        'PYOPENGL_USE_ACCELERATE=0',
    )
    def test_attaching_a_texture_does_not_raise(self):
        self.require_extension('GL_EXT_framebuffer_object')
        tex = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glBindTexture(GL_TEXTURE_2D, 0)

        fbo = int(glGenFramebuffersEXT(1))
        with self.framebuffer(fbo):
            glBindTexture(GL_TEXTURE_2D, tex)
            glFramebufferTexture2DEXT(
                GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_2D, tex, 0
            )
        self.check_error('attaching a texture to an EXT framebuffer')
        glDeleteTextures(1, object_names(tex))
        glDeleteFramebuffersEXT(1, object_names(fbo))


if __name__ == '__main__':
    unittest.main()
