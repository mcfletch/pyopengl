#! /usr/bin/env python3
"""NVIDIA desktop-GL advanced extensions: mesh shading, the command-list
(bindless command buffer) API, single-GPU multicast surface, timeline
semaphores and GPU-resource queries.

Functional tests -- real objects and real calls with a clean error state.
Extensions whose entry points only operate on externally-imported resources
(Vulkan images/fences, imported memory objects) cannot succeed headless and are
skipped with a reason rather than smoke-probed.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403

MESH = '''#version 450
#extension GL_NV_mesh_shader : require
layout(local_size_x=1) in;
layout(triangles, max_vertices=3, max_primitives=1) out;
void main(){
    gl_PrimitiveCountNV = 1u;
    gl_MeshVerticesNV[0].gl_Position = vec4(-1.0, -1.0, 0.0, 1.0);
    gl_MeshVerticesNV[1].gl_Position = vec4( 3.0, -1.0, 0.0, 1.0);
    gl_MeshVerticesNV[2].gl_Position = vec4(-1.0,  3.0, 0.0, 1.0);
    gl_PrimitiveIndicesNV[0] = 0;
    gl_PrimitiveIndicesNV[1] = 1;
    gl_PrimitiveIndicesNV[2] = 2;
}'''
MESH_FRAG = '#version 450\nout vec4 c; void main(){ c = vec4(1.0); }'


class TestNVAdvanced(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def _color_fbo(self, w=8, h=8):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, w, h)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        glViewport(0, 0, w, h)
        return fbo

    # --- GL_NV_mesh_shader -----------------------------------------------
    def test_nv_mesh_shader(self):
        self.require_extension('GL_NV_mesh_shader')
        from OpenGL.GL.NV.mesh_shader import (
            glDrawMeshTasksNV, glDrawMeshTasksIndirectNV,
            glMultiDrawMeshTasksIndirectNV, glMultiDrawMeshTasksIndirectCountNV,
            GL_MESH_SHADER_NV,
        )
        from OpenGL.GL import shaders

        program = shaders.compileProgram(
            shaders.compileShader(MESH, GL_MESH_SHADER_NV),
            shaders.compileShader(MESH_FRAG, GL_FRAGMENT_SHADER),
        )
        self._color_fbo()
        glUseProgram(program)
        glDrawMeshTasksNV(0, 1)

        indirect = one(glGenBuffers(1))
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, indirect)
        glBufferData(GL_DRAW_INDIRECT_BUFFER, np.array([1, 0], 'u4'), GL_STATIC_DRAW)
        glDrawMeshTasksIndirectNV(0)
        glMultiDrawMeshTasksIndirectNV(0, 1, 0)

        param = one(glGenBuffers(1))
        glBindBuffer(GL_PARAMETER_BUFFER, param)
        glBufferData(GL_PARAMETER_BUFFER, np.array([0], 'u4'), GL_STATIC_DRAW)
        glMultiDrawMeshTasksIndirectCountNV(0, 0, 0, 0)

        glBindBuffer(GL_PARAMETER_BUFFER, 0)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, 0)
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('nv mesh shader')

    # --- GL_NV_command_list ----------------------------------------------
    def test_nv_command_list(self):
        self.require_extension('GL_NV_command_list')
        from OpenGL.GL.NV.command_list import (
            glCreateCommandListsNV, glDeleteCommandListsNV, glIsCommandListNV,
            glCommandListSegmentsNV, glCompileCommandListNV, glCallCommandListNV,
            glCreateStatesNV, glDeleteStatesNV, glIsStateNV, glStateCaptureNV,
            glGetCommandHeaderNV, glGetStageIndexNV, glDrawCommandsNV,
            glDrawCommandsAddressNV, glDrawCommandsStatesNV,
            glDrawCommandsStatesAddressNV, glListDrawCommandsStatesClientNV,
            GL_NOP_COMMAND_NV,
        )

        lists = np.zeros(1, 'u4')
        glCreateCommandListsNV(1, lists)
        clist = int(lists[0])
        self.assertTrue(glIsCommandListNV(clist))
        glCommandListSegmentsNV(clist, 1)

        states = np.zeros(1, 'u4')
        glCreateStatesNV(1, states)
        state = int(states[0])
        self.assertTrue(glIsStateNV(state))
        # state capture snapshots the *current* draw pipeline, so bind one
        self._color_fbo()
        program = self.compile_program(
            '#version 450 core\nvoid main(){gl_Position=vec4(0.0,0.0,0.0,1.0);}',
            '#version 450 core\nout vec4 c;void main(){c=vec4(1.0);}',
        )
        glUseProgram(program)
        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        glStateCaptureNV(state, GL_TRIANGLES)

        glGetCommandHeaderNV(GL_NOP_COMMAND_NV, 4)
        glGetStageIndexNV(GL_FRAGMENT_SHADER)

        # zero-count client-side replay is a well-defined no-op
        glListDrawCommandsStatesClientNV(clist, 0, None, None, None, None, 0)
        glCompileCommandListNV(clist)
        glCallCommandListNV(clist)
        # glDrawCommands{,Address,States,StatesAddress}NV require a populated GPU
        # token buffer (a valid command sequence) to drive without error, which
        # is beyond a state-only smoke test, so they are not exercised here.

        glDeleteStatesNV(1, states)
        glDeleteCommandListsNV(1, lists)
        self.check_error('nv command list')

    # --- GL_NV_gpu_multicast ---------------------------------------------
    def test_nv_gpu_multicast(self):
        self.require_extension('GL_NV_gpu_multicast')
        # Every multicast command (even glRenderGpuMaskNV) is GL_INVALID_OPERATION
        # on a single device -- the extension requires two or more linked GPUs.
        self.skipTest('GL_NV_gpu_multicast requires two or more linked GPUs (SLI)')

    # --- GL_NV_timeline_semaphore ----------------------------------------
    def test_nv_timeline_semaphore(self):
        self.require_extension('GL_NV_timeline_semaphore')
        from OpenGL.GL.NV.timeline_semaphore import (
            glCreateSemaphoresNV, glSemaphoreParameterivNV, glGetSemaphoreParameterivNV,
            GL_SEMAPHORE_TYPE_NV, GL_SEMAPHORE_TYPE_TIMELINE_NV,
        )

        sems = np.zeros(1, 'u4')
        glCreateSemaphoresNV(1, sems)
        sem = int(sems[0])
        glSemaphoreParameterivNV(sem, GL_SEMAPHORE_TYPE_NV, np.array([GL_SEMAPHORE_TYPE_TIMELINE_NV], 'i'))
        glGetSemaphoreParameterivNV(sem, GL_SEMAPHORE_TYPE_NV, np.zeros(1, 'i'))
        self.check_error('nv timeline semaphore')

    # --- GL_NV_query_resource_tag ----------------------------------------
    def test_nv_query_resource_tag(self):
        self.require_extension('GL_NV_query_resource_tag')
        from OpenGL.GL.NV.query_resource_tag import (
            glGenQueryResourceTagNV, glDeleteQueryResourceTagNV, glQueryResourceTagNV,
        )

        tags = np.zeros(1, 'i')
        glGenQueryResourceTagNV(1, tags)
        tag = int(tags[0])
        glQueryResourceTagNV(tag, b'pyopengl-test')
        glDeleteQueryResourceTagNV(1, tags)
        self.check_error('nv query resource tag')

    def test_nv_query_resource(self):
        self.require_extension('GL_NV_query_resource')
        self.skipTest('GPU resource enumeration is unavailable on a headless device context')

    # --- interop-only extensions -----------------------------------------
    def test_nv_memory_attachment(self):
        self.require_extension('GL_NV_memory_attachment')
        self.skipTest('attaching memory objects requires externally-imported memory')

    def test_nv_memory_object_sparse(self):
        self.require_extension('GL_NV_memory_object_sparse')
        self.skipTest('memory-backed sparse commitment requires imported memory objects')

    def test_nv_draw_vulkan_image(self):
        self.require_extension('GL_NV_draw_vulkan_image')
        self.skipTest('Vulkan image/fence/semaphore interop is unavailable headless')


if __name__ == '__main__':
    unittest.main()
