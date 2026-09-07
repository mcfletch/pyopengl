#! /usr/bin/env python3
"""GLES3.0: sampler objects and fence sync objects."""

import unittest
from arraycompat import np, object_names, one

from arraycompat import copy_safe
from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_NEAREST,
    GL_LINEAR,
    GL_CLAMP_TO_EDGE,
    GL_SYNC_GPU_COMMANDS_COMPLETE,
    GL_SYNC_FLUSH_COMMANDS_BIT,
    GL_SYNC_STATUS,
    GL_ALREADY_SIGNALED,
    GL_CONDITION_SATISFIED,
    GL_TIMEOUT_EXPIRED,
    glGenSamplers,
    glBindSampler,
    glIsSampler,
    glDeleteSamplers,
    glSamplerParameteri,
    glSamplerParameterf,
    glSamplerParameteriv,
    glSamplerParameterfv,
    glGetSamplerParameteriv,
    glGetSamplerParameterfv,
    glFenceSync,
    glIsSync,
    glClientWaitSync,
    glWaitSync,
    glGetSynciv,
    glDeleteSync,
    glFlush,
)

GL_TIMEOUT_IGNORED = 0xFFFFFFFFFFFFFFFF


class TestES3SamplersSync(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_samplers(self):
        sampler = one(glGenSamplers(1))
        glBindSampler(0, sampler)
        glSamplerParameteri(sampler, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glSamplerParameterf(sampler, GL_TEXTURE_MAG_FILTER, float(GL_LINEAR))
        glSamplerParameteriv(
            sampler, GL_TEXTURE_WRAP_S, copy_safe([int(GL_CLAMP_TO_EDGE)], 'i')
        )
        glSamplerParameterfv(
            sampler, GL_TEXTURE_WRAP_S, copy_safe([float(GL_CLAMP_TO_EDGE)], 'f')
        )
        self.assertTrue(glIsSampler(sampler))

        ibuf = np.zeros(1, 'i')
        glGetSamplerParameteriv(sampler, GL_TEXTURE_MIN_FILTER, ibuf)
        self.assertEqual(int(ibuf[0]), int(GL_NEAREST))
        fbuf = np.zeros(1, 'f')
        glGetSamplerParameterfv(sampler, GL_TEXTURE_MAG_FILTER, fbuf)
        self.assertEqual(int(fbuf[0]), int(GL_LINEAR))
        self.check_error('samplers')

        glBindSampler(0, 0)
        glDeleteSamplers(1, object_names(sampler))

    def test_sync(self):
        sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
        self.assertTrue(glIsSync(sync))
        glFlush()
        status = glClientWaitSync(sync, GL_SYNC_FLUSH_COMMANDS_BIT, 10**9)
        self.assertIn(
            int(status),
            (
                int(GL_ALREADY_SIGNALED),
                int(GL_CONDITION_SATISFIED),
                int(GL_TIMEOUT_EXPIRED),
            ),
        )
        glWaitSync(sync, 0, GL_TIMEOUT_IGNORED)

        length = np.zeros(1, 'i')
        values = np.zeros(1, 'i')
        glGetSynciv(sync, GL_SYNC_STATUS, 1, length, values)
        self.check_error('sync')
        glDeleteSync(sync)


if __name__ == '__main__':
    unittest.main()
