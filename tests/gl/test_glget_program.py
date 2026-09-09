#! /usr/bin/env python3
"""glGet size coverage for the object-scoped ``program`` and ``shader`` getter
families (``glGetProgramiv`` / ``glGetShaderiv``), which the live state sweep in
test_glget_extensions.py cannot reach (they need a real program/shader object).

Both getters consume ``_glget_size_mapping``, so a wrong CSV size truncates or
over-allocates the result.  This builds a real multi-stage program (vertex +
geometry + fragment, and a separate compute program) plus a standalone shader,
then for every ``program``/``shader`` pname the registry defines it measures the
true number of ints the driver writes (int sentinel probe) and checks it against
glgetsizes.csv.  pnames needing setup this fixture doesn't provide (transform
feedback varyings, program binary) are skipped, not failed.
"""

import ctypes
import unittest

from gltestcase import GLTestCase
from glget_check import GLGetCheckMixin, expected_count

from OpenGL.GL import *  # noqa: F401,F403

_VS = '#version 330 core\nvoid main(){ gl_Position = vec4(0.0); }\n'
_GS = ('#version 330 core\nlayout(triangles) in;\n'
       'layout(triangle_strip, max_vertices=3) out;\n'
       'void main(){ for(int i=0;i<3;i++){ gl_Position = gl_in[i].gl_Position; '
       'EmitVertex(); } EndPrimitive(); }\n')
_FS = '#version 330 core\nout vec4 c;\nvoid main(){ c = vec4(1.0); }\n'
_CS = ('#version 430\nlayout(local_size_x=4,local_size_y=2,local_size_z=1) in;\n'
       'void main(){}\n')


class TestProgramGLGet(GLGetCheckMixin, GLTestCase):
    profile = 'core'
    gl_version = (3, 3)
    glget_suite = 'gl'

    def _compile(self, kind_enum, src):
        sh = glCreateShader(kind_enum)
        glShaderSource(sh, src)
        glCompileShader(sh)
        if not glGetShaderiv(sh, GL_COMPILE_STATUS):
            self.fail('compile failed: %s' % glGetShaderInfoLog(sh))
        return sh

    def _link(self, shaders):
        prog = glCreateProgram()
        for sh in shaders:
            glAttachShader(prog, sh)
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            self.fail('link failed: %s' % glGetProgramInfoLog(prog))
        self.addCleanup(glDeleteProgram, prog)
        return prog

    def setUp(self):
        super().setUp()
        self._gfx = self._link([
            self._compile(GL_VERTEX_SHADER, _VS),
            self._compile(GL_GEOMETRY_SHADER, _GS),
            self._compile(GL_FRAGMENT_SHADER, _FS),
        ])
        self._shader = self._compile(GL_FRAGMENT_SHADER, _FS)
        self._compute = None
        if self.version() >= (4, 3):
            self._compute = self._link([self._compile(GL_COMPUTE_SHADER, _CS)])

    def _descs(self, family):
        out, seen = [], set()
        for kind in ('features', 'extensions'):
            import glget_check
            data = glget_check.load_groups('gl')
            for _name, info in data[kind].items():
                for d in info['glgets']:
                    if d['family'] == family and d['value'] not in seen:
                        seen.add(d['value'])
                        out.append(d)
        return out

    def test_program_property_sizes(self):
        checked = 0
        for d in self._descs('program'):
            value = int(d['value'], 16)
            want = expected_count(d['size'])
            if want is None:
                continue
            prog = self._compute if d['name'] == 'GL_COMPUTE_WORK_GROUP_SIZE' else self._gfx
            if prog is None:
                continue
            ts = self.probe_int_size(lambda buf, v=value, p=prog: glGetProgramiv(p, v, buf))
            with self.subTest(pname=d['name']):
                if ts is None or ts == 'overflow':
                    self.skipTest('%s not queryable on this program/driver' % d['name'])
                self.assertEqual(
                    ts, want,
                    '%s: glGetProgramiv writes %d, glgetsizes.csv says %s (=%d)'
                    % (d['name'], ts, d['size'].split('#')[0].strip(), want))
                checked += 1
        self.assertTrue(checked, 'no program-property pnames exercised')

    def test_shader_property_sizes(self):
        for d in self._descs('shader'):
            value = int(d['value'], 16)
            want = expected_count(d['size'])
            if want is None:
                continue
            ts = self.probe_int_size(
                lambda buf, v=value: glGetShaderiv(self._shader, v, buf))
            with self.subTest(pname=d['name']):
                if ts is None or ts == 'overflow':
                    self.skipTest('%s not queryable on this shader/driver' % d['name'])
                self.assertEqual(
                    ts, want,
                    '%s: glGetShaderiv writes %d, glgetsizes.csv says %s (=%d)'
                    % (d['name'], ts, d['size'].split('#')[0].strip(), want))


if __name__ == '__main__':
    unittest.main()
