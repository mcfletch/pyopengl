#! /usr/bin/env python3
"""Query-object extensions: timer queries, boolean occlusion queries,
conditional render, APPLE fence sync, parallel shader compile."""

import unittest
import ctypes
from arraycompat import np, object_names

from egltestcase import ESTestCase
from OpenGL.GLES2.EXT import disjoint_timer_query as timer
from OpenGL.GLES2.EXT import occlusion_query_boolean as occ
from OpenGL.GLES2.NV import conditional_render as cond
from OpenGL.GLES2.KHR import parallel_shader_compile as psc
from OpenGL.GLES2.APPLE import sync as apple
from OpenGL.GLES3 import (
    GL_SYNC_GPU_COMMANDS_COMPLETE,
    GL_SYNC_STATUS,
    GL_MAX_SERVER_WAIT_TIMEOUT,
)


class TestQueryExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_disjoint_timer_query(self):
        self.require_extension('GL_EXT_disjoint_timer_query')
        with self.exercise():
            ids = np.zeros(1, 'u4')
            timer.glGenQueriesEXT(1, ids)
            q = int(ids[0])
            timer.glIsQueryEXT(q)
            timer.glQueryCounterEXT(q, timer.GL_TIMESTAMP_EXT)
            avail = np.zeros(1, 'i')
            timer.glGetQueryObjectivEXT(q, timer.GL_QUERY_RESULT_AVAILABLE_EXT, avail)
            res_u = np.zeros(1, 'u4')
            timer.glGetQueryObjectuivEXT(q, timer.GL_QUERY_RESULT_EXT, res_u)
            # 64-bit query getters now work with a numpy 'Q'/'q' array, a ctypes
            # buffer, or auto-allocation (issue #9 fixed); ctypes buffers here.
            res_i64 = (ctypes.c_int64 * 1)()
            timer.glGetQueryObjecti64vEXT(q, timer.GL_QUERY_RESULT_EXT, res_i64)
            res_u64 = (ctypes.c_uint64 * 1)()
            timer.glGetQueryObjectui64vEXT(q, timer.GL_QUERY_RESULT_EXT, res_u64)
            qiv = np.zeros(1, 'i')
            timer.glGetQueryivEXT(
                timer.GL_TIMESTAMP_EXT, timer.GL_QUERY_COUNTER_BITS_EXT, qiv
            )
            big = np.zeros(1, 'q')
            timer.glGetInteger64vEXT(timer.GL_TIMESTAMP_EXT, big)
            # an elapsed-time query around nothing
            timer.glBeginQueryEXT(timer.GL_TIME_ELAPSED_EXT, q)
            timer.glEndQueryEXT(timer.GL_TIME_ELAPSED_EXT)
            timer.glDeleteQueriesEXT(1, object_names(q))
            self.check_error('timer query')

    def test_occlusion_query_boolean(self):
        self.require_extension('GL_EXT_occlusion_query_boolean')
        with self.exercise():
            ids = np.zeros(1, 'u4')
            occ.glGenQueriesEXT(1, ids)
            q = int(ids[0])
            occ.glBeginQueryEXT(occ.GL_ANY_SAMPLES_PASSED_EXT, q)
            occ.glEndQueryEXT(occ.GL_ANY_SAMPLES_PASSED_EXT)
            occ.glIsQueryEXT(q)
            cur = np.zeros(1, 'i')
            occ.glGetQueryivEXT(
                occ.GL_ANY_SAMPLES_PASSED_EXT, occ.GL_CURRENT_QUERY_EXT, cur
            )
            res = np.zeros(1, 'u4')
            occ.glGetQueryObjectuivEXT(q, occ.GL_QUERY_RESULT_EXT, res)
            occ.glDeleteQueriesEXT(1, object_names(q))
            self.check_error('occlusion query')

    def test_nv_conditional_render(self):
        self.require_extension('GL_NV_conditional_render')
        with self.exercise():
            from OpenGL.GLES3 import glGenQueries, glDeleteQueries

            q = glGenQueries(1)
            cond.glBeginConditionalRenderNV(q, cond.GL_QUERY_WAIT_NV)
            cond.glEndConditionalRenderNV()
            glDeleteQueries(1, object_names(q))
            self.check_error('conditional render')

    def test_khr_parallel_shader_compile(self):
        self.require_extension('GL_KHR_parallel_shader_compile')
        with self.exercise():
            psc.glMaxShaderCompilerThreadsKHR(2)
            self.check_error('parallel shader compile')

    def test_apple_sync(self):
        self.require_extension('GL_APPLE_sync')
        with self.exercise():
            sync = apple.glFenceSyncAPPLE(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
            apple.glIsSyncAPPLE(sync)
            apple.glClientWaitSyncAPPLE(sync, 0, 0)
            apple.glWaitSyncAPPLE(sync, 0, 0xFFFFFFFFFFFFFFFF)
            length = np.zeros(1, 'i')
            values = np.zeros(1, 'i')
            apple.glGetSyncivAPPLE(sync, GL_SYNC_STATUS, 1, length, values)
            big = np.zeros(1, 'q')
            apple.glGetInteger64vAPPLE(GL_MAX_SERVER_WAIT_TIMEOUT, big)
            apple.glDeleteSyncAPPLE(sync)
            self.check_error('apple sync')


if __name__ == '__main__':
    unittest.main()
