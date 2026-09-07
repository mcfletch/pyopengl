#! /usr/bin/env python3
"""EXT desktop-GL extensions the NVIDIA driver exposes beyond the Mesa baseline:
EXT separable program objects, external-semaphore object management, image
load/store, bindable uniforms, depth-bounds test, EXT geometry-shader4 program
parameter, raster multisample and window rectangles.

Functional tests -- real objects and real calls with a clean error state.  A few
entry points in these extensions only operate on externally-imported resources
(Vulkan/Direct3D semaphores) and cannot succeed in a headless unit test; those
are skipped with a reason rather than smoke-probed, and are not counted as
covered.
"""

import unittest
import ctypes
from arraycompat import np, object_names

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


SEP_FRAGMENT = '''#version 420
uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
out vec4 c;
void main() {
    c = vec4(uf + uv2.x + uv3.y + uv4.z) + vec4(float(ui + ui2.x + ui3.y + ui4.z))
      + vec4(float(uu + uu2.x + uu3.y + uu4.z))
      + vec4(m2[0][0]+m3[0][0]+m4[0][0]+m23[0][0]+m32[0][0]+m24[0][0]+m42[0][0]+m34[0][0]+m43[0][0]);
}'''


class TestEXTExtra(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    # --- GL_EXT_separate_shader_objects ----------------------------------
    def test_ext_separate_shader_objects(self):
        self.require_extension('GL_EXT_separate_shader_objects')
        from OpenGL.GL.EXT.separate_shader_objects import (
            glCreateShaderProgramvEXT, glCreateShaderProgramEXT,
            glGenProgramPipelinesEXT, glBindProgramPipelineEXT,
            glUseProgramStagesEXT, glActiveShaderProgramEXT,
            glActiveProgramEXT, glUseShaderProgramEXT,
            glValidateProgramPipelineEXT, glGetProgramPipelineivEXT,
            glGetProgramPipelineInfoLogEXT, glIsProgramPipelineEXT,
            glDeleteProgramPipelinesEXT, glProgramParameteriEXT,
            glProgramUniform1fEXT, glProgramUniform2fEXT, glProgramUniform3fEXT,
            glProgramUniform4fEXT, glProgramUniform1iEXT, glProgramUniform2iEXT,
            glProgramUniform3iEXT, glProgramUniform4iEXT, glProgramUniform1uiEXT,
            glProgramUniform2uiEXT, glProgramUniform3uiEXT, glProgramUniform4uiEXT,
            glProgramUniform1fvEXT, glProgramUniform2fvEXT, glProgramUniform3fvEXT,
            glProgramUniform4fvEXT, glProgramUniform1ivEXT, glProgramUniform2ivEXT,
            glProgramUniform3ivEXT, glProgramUniform4ivEXT, glProgramUniform1uivEXT,
            glProgramUniform2uivEXT, glProgramUniform3uivEXT, glProgramUniform4uivEXT,
            glProgramUniformMatrix2fvEXT, glProgramUniformMatrix3fvEXT,
            glProgramUniformMatrix4fvEXT, glProgramUniformMatrix2x3fvEXT,
            glProgramUniformMatrix3x2fvEXT, glProgramUniformMatrix2x4fvEXT,
            glProgramUniformMatrix4x2fvEXT, glProgramUniformMatrix3x4fvEXT,
            glProgramUniformMatrix4x3fvEXT,
            GL_PROGRAM_SEPARABLE_EXT, GL_ACTIVE_PROGRAM_EXT,
        )

        p = glCreateShaderProgramvEXT(GL_FRAGMENT_SHADER, 1, _char_pp([SEP_FRAGMENT]))
        # the single-string convenience entry point and the legacy v1 API
        p2 = glCreateShaderProgramEXT(GL_FRAGMENT_SHADER, SEP_FRAGMENT)
        glProgramParameteriEXT(p, GL_PROGRAM_SEPARABLE_EXT, GL_TRUE)

        pids = np.zeros(1, 'u4')
        glGenProgramPipelinesEXT(1, pids)
        pipeline = int(pids[0])
        glBindProgramPipelineEXT(pipeline)
        glUseProgramStagesEXT(pipeline, GL_FRAGMENT_SHADER_BIT, p)
        glActiveShaderProgramEXT(pipeline, p)
        self.assertTrue(glIsProgramPipelineEXT(pipeline))
        glValidateProgramPipelineEXT(pipeline)
        info = np.zeros(1, 'i')
        glGetProgramPipelineivEXT(pipeline, GL_ACTIVE_PROGRAM_EXT, info)
        length = (ctypes.c_int * 1)()
        log = (ctypes.c_char * 256)()
        glGetProgramPipelineInfoLogEXT(pipeline, 256, length, log)

        # legacy (v1) separable API: install a program on the fixed pipeline
        glUseShaderProgramEXT(GL_FRAGMENT_SHADER, p)
        glActiveProgramEXT(p)
        glUseShaderProgramEXT(GL_FRAGMENT_SHADER, 0)

        def loc(n):
            return glGetUniformLocation(p, n)

        glProgramUniform1fEXT(p, loc('uf'), 1.0)
        glProgramUniform2fEXT(p, loc('uv2'), 1.0, 2.0)
        glProgramUniform3fEXT(p, loc('uv3'), 1.0, 2.0, 3.0)
        glProgramUniform4fEXT(p, loc('uv4'), 1.0, 2.0, 3.0, 4.0)
        glProgramUniform1iEXT(p, loc('ui'), 1)
        glProgramUniform2iEXT(p, loc('ui2'), 1, 2)
        glProgramUniform3iEXT(p, loc('ui3'), 1, 2, 3)
        glProgramUniform4iEXT(p, loc('ui4'), 1, 2, 3, 4)
        glProgramUniform1uiEXT(p, loc('uu'), 1)
        glProgramUniform2uiEXT(p, loc('uu2'), 1, 2)
        glProgramUniform3uiEXT(p, loc('uu3'), 1, 2, 3)
        glProgramUniform4uiEXT(p, loc('uu4'), 1, 2, 3, 4)
        glProgramUniform1fvEXT(p, loc('uf'), 1, np.array([1], 'f'))
        glProgramUniform2fvEXT(p, loc('uv2'), 1, np.array([1, 2], 'f'))
        glProgramUniform3fvEXT(p, loc('uv3'), 1, np.array([1, 2, 3], 'f'))
        glProgramUniform4fvEXT(p, loc('uv4'), 1, np.array([1, 2, 3, 4], 'f'))
        glProgramUniform1ivEXT(p, loc('ui'), 1, np.array([1], 'i'))
        glProgramUniform2ivEXT(p, loc('ui2'), 1, np.array([1, 2], 'i'))
        glProgramUniform3ivEXT(p, loc('ui3'), 1, np.array([1, 2, 3], 'i'))
        glProgramUniform4ivEXT(p, loc('ui4'), 1, np.array([1, 2, 3, 4], 'i'))
        glProgramUniform1uivEXT(p, loc('uu'), 1, np.array([1], 'u4'))
        glProgramUniform2uivEXT(p, loc('uu2'), 1, np.array([1, 2], 'u4'))
        glProgramUniform3uivEXT(p, loc('uu3'), 1, np.array([1, 2, 3], 'u4'))
        glProgramUniform4uivEXT(p, loc('uu4'), 1, np.array([1, 2, 3, 4], 'u4'))
        glProgramUniformMatrix2fvEXT(p, loc('m2'), 1, False, np.eye(2, dtype='f'))
        glProgramUniformMatrix3fvEXT(p, loc('m3'), 1, False, np.eye(3, dtype='f'))
        glProgramUniformMatrix4fvEXT(p, loc('m4'), 1, False, np.eye(4, dtype='f'))
        glProgramUniformMatrix2x3fvEXT(p, loc('m23'), 1, False, np.zeros((2, 3), 'f'))
        glProgramUniformMatrix3x2fvEXT(p, loc('m32'), 1, False, np.zeros((3, 2), 'f'))
        glProgramUniformMatrix2x4fvEXT(p, loc('m24'), 1, False, np.zeros((2, 4), 'f'))
        glProgramUniformMatrix4x2fvEXT(p, loc('m42'), 1, False, np.zeros((4, 2), 'f'))
        glProgramUniformMatrix3x4fvEXT(p, loc('m34'), 1, False, np.zeros((3, 4), 'f'))
        glProgramUniformMatrix4x3fvEXT(p, loc('m43'), 1, False, np.zeros((4, 3), 'f'))

        glBindProgramPipelineEXT(0)
        glDeleteProgramPipelinesEXT(1, object_names(pipeline))
        glDeleteProgram(p)
        glDeleteProgram(p2)
        self.check_error('ext separate shader objects')

    # --- GL_EXT_semaphore ------------------------------------------------
    def test_ext_semaphore(self):
        self.require_extension('GL_EXT_semaphore')
        from OpenGL.GL.EXT.semaphore import (
            glGenSemaphoresEXT, glDeleteSemaphoresEXT, glIsSemaphoreEXT,
            glGetUnsignedBytevEXT, glGetUnsignedBytei_vEXT,
        )
        from OpenGL.GL.EXT.memory_object import (
            GL_DRIVER_UUID_EXT, GL_DEVICE_UUID_EXT, GL_NUM_DEVICE_UUIDS_EXT,
        )

        sems = np.zeros(2, 'u4')
        glGenSemaphoresEXT(2, sems)
        # glIsSemaphoreEXT only reports TRUE once a semaphore has been imported
        # from an external handle, so a freshly-generated name reads as not-a-
        # semaphore (like glIsTexture before first bind); just exercise the query.
        glIsSemaphoreEXT(int(sems[0]))
        glGetUnsignedBytevEXT(GL_DRIVER_UUID_EXT, np.zeros(16, 'B'))
        count = int(self.getInteger(GL_NUM_DEVICE_UUIDS_EXT))
        if count:
            glGetUnsignedBytei_vEXT(GL_DEVICE_UUID_EXT, 0, np.zeros(16, 'B'))
        glDeleteSemaphoresEXT(2, sems)
        self.check_error('ext semaphore')
        # Signalling/waiting and the D3D12 fence parameter only apply to
        # externally-imported (Vulkan/Direct3D) semaphores; not testable here.

    def test_ext_semaphore_fd(self):
        self.require_extension('GL_EXT_semaphore_fd')
        self.skipTest('importing a semaphore requires an external Vulkan/opaque fd')

    # --- GL_EXT_shader_image_load_store ----------------------------------
    def test_ext_shader_image_load_store(self):
        self.require_extension('GL_EXT_shader_image_load_store')
        from OpenGL.GL.EXT.shader_image_load_store import (
            glBindImageTextureEXT, glMemoryBarrierEXT,
            GL_ALL_BARRIER_BITS_EXT,
        )

        tex = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        glBindImageTextureEXT(0, tex, 0, GL_FALSE, 0, GL_READ_WRITE, GL_RGBA8)
        glMemoryBarrierEXT(GL_ALL_BARRIER_BITS_EXT)
        self.check_error('ext shader image load store')

    # --- GL_EXT_bindable_uniform -----------------------------------------
    def test_ext_bindable_uniform(self):
        self.require_extension('GL_EXT_bindable_uniform')
        from OpenGL.GL.EXT.bindable_uniform import (
            glGetUniformBufferSizeEXT, glGetUniformOffsetEXT, glUniformBufferEXT,
        )

        program = self.compile_program(
            '#version 120\n'
            '#extension GL_EXT_bindable_uniform : require\n'
            'bindable uniform vec4 bu[8];\n'
            'void main(){ gl_Position = bu[0]; }',
            '#version 120\nvoid main(){ gl_FragColor = vec4(1.0); }',
        )
        loc = glGetUniformLocation(program, 'bu')
        size = int(glGetUniformBufferSizeEXT(program, loc))
        self.assertGreater(size, 0)
        glGetUniformOffsetEXT(program, loc)
        buf = int(glGenBuffers(1))
        glBindBuffer(GL_UNIFORM_BUFFER, buf)
        glBufferData(GL_UNIFORM_BUFFER, size, None, GL_DYNAMIC_DRAW)
        glUseProgram(program)
        glUniformBufferEXT(program, loc, buf)
        glUseProgram(0)
        self.check_error('ext bindable uniform')

    # --- GL_EXT_depth_bounds_test ----------------------------------------
    def test_ext_depth_bounds_test(self):
        self.require_extension('GL_EXT_depth_bounds_test')
        from OpenGL.GL.EXT.depth_bounds_test import (
            glDepthBoundsEXT, GL_DEPTH_BOUNDS_TEST_EXT,
        )

        glEnable(GL_DEPTH_BOUNDS_TEST_EXT)
        glDepthBoundsEXT(0.0, 1.0)
        glDisable(GL_DEPTH_BOUNDS_TEST_EXT)
        self.check_error('ext depth bounds test')

    # --- GL_EXT_geometry_shader4 -----------------------------------------
    def test_ext_geometry_shader4(self):
        self.require_extension('GL_EXT_geometry_shader4')
        from OpenGL.GL.EXT.geometry_shader4 import (
            glProgramParameteriEXT, GL_GEOMETRY_VERTICES_OUT_EXT,
            GL_GEOMETRY_INPUT_TYPE_EXT, GL_GEOMETRY_OUTPUT_TYPE_EXT,
        )

        program = int(glCreateProgram())
        glProgramParameteriEXT(program, GL_GEOMETRY_VERTICES_OUT_EXT, 3)
        glProgramParameteriEXT(program, GL_GEOMETRY_INPUT_TYPE_EXT, GL_POINTS)
        glProgramParameteriEXT(program, GL_GEOMETRY_OUTPUT_TYPE_EXT, GL_TRIANGLE_STRIP)
        glDeleteProgram(program)
        self.check_error('ext geometry_shader4')

    # --- GL_EXT_raster_multisample ---------------------------------------
    def test_ext_raster_multisample(self):
        self.require_extension('GL_EXT_raster_multisample')
        from OpenGL.GL.EXT.raster_multisample import glRasterSamplesEXT

        glRasterSamplesEXT(4, GL_TRUE)
        glRasterSamplesEXT(0, GL_FALSE)
        self.check_error('ext raster multisample')

    # --- GL_EXT_window_rectangles ----------------------------------------
    def test_ext_window_rectangles(self):
        self.require_extension('GL_EXT_window_rectangles')
        from OpenGL.GL.EXT.window_rectangles import (
            glWindowRectanglesEXT, GL_INCLUSIVE_EXT, GL_EXCLUSIVE_EXT,
        )

        rects = np.array([0, 0, 4, 4], 'i')
        glWindowRectanglesEXT(GL_EXCLUSIVE_EXT, 1, rects)
        glWindowRectanglesEXT(GL_INCLUSIVE_EXT, 1, rects)
        glWindowRectanglesEXT(GL_EXCLUSIVE_EXT, 0, None)
        self.check_error('ext window rectangles')


if __name__ == '__main__':
    unittest.main()
