#! /usr/bin/env python3
"""Audit glGet output sizes against the live driver (no pytest).

Creates a context, then for every ``state`` pname of every supported version and
extension, measures the true number of values the driver writes (funky-float
sentinel probe) and compares it to ``glgetsizes.csv``.  Prints a mismatch report
-- the worklist for correcting the CSV (over- and under-allocations alike).

    TEST_WINDOWING=egl  python glget_audit.py gl      # NVIDIA, desktop GL
    TEST_WINDOWING=glfw python glget_audit.py gl      # llvmpipe, desktop GL
    TEST_WINDOWING=egl  python glget_audit.py gles
"""

import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mirror conftest.py: the headless EGL-device backend loads GL entry points
# through EGL, so PYOPENGL_PLATFORM must be set before anything imports OpenGL.
import backends  # noqa: E402 -- needs the sys.path entry above

if backends.requested() == 'egl':
    os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')

import glcontext
from glget_check import (
    load_groups, parse_size, expected_count, crashes, INDEXED_STATE,
    BYTE_ARRAY_STATE, _SENTINELS, _PROBE_LEN,
)
from OpenGL import error


def make_case(suite):
    if suite == 'gl':
        import glcontext_desktop as m
        base, kw = m.DesktopGLTestCaseBase, dict(profile='compatibility', gl_version=(4, 5))
    else:
        import glcontext_es as m
        base, kw = m.ESTestCaseBase, dict(gl_version=(3, 2))
    cls = type('AuditCase', (glcontext.pick_backend(), base), kw)
    case = cls()
    case.setUp()
    return case


def true_size(gl, value):
    counts = []
    for raw in _SENTINELS:
        sent = ctypes.c_float(raw).value
        buf = (ctypes.c_float * _PROBE_LEN)(*([sent] * _PROBE_LEN))
        try:
            gl.glGetFloatv(value, buf)
        except error.GLError as err:
            while gl.glGetError() != gl.GL_NO_ERROR:
                pass
            if err.err in (gl.GL_INVALID_ENUM, gl.GL_INVALID_OPERATION):
                return None
            return ('err', err.err)
        while gl.glGetError() != gl.GL_NO_ERROR:
            pass
        changed = [i for i in range(_PROBE_LEN) if buf[i] != sent]
        counts.append((max(changed) + 1) if changed else 0)
    if counts[0] != counts[1]:
        return None
    return counts[0]


def main(argv):
    suite = (argv[0] if argv else 'gl')
    case = make_case(suite)
    gl = case.gl
    present_ext = case.extensions()
    data = load_groups(suite)

    verified_only = '--verified' in argv
    seen, mismatches, verified, probed = {}, [], [], 0
    for kind in ('features', 'extensions'):
        for name, info in sorted(data[kind].items()):
            if kind == 'extensions' and name not in present_ext:
                continue
            for d in info['glgets']:
                if d['family'] not in ('state', 'state?'):
                    continue
                v = int(d['value'], 16)
                if (crashes(v) or d['name'] in INDEXED_STATE
                        or d['name'] in BYTE_ARRAY_STATE or v in seen):
                    continue
                seen[v] = d['name']
                ts = true_size(gl, v)
                if ts is None or isinstance(ts, tuple):
                    continue
                probed += 1
                want = expected_count(d['size'])
                if want is None:
                    continue
                if ts != want:
                    kindword = 'OVER ' if want > ts else 'UNDER'
                    mismatches.append((kindword, d['name'], d['value'], want, ts))
                else:
                    verified.append(d['name'])
    case.tearDown()

    if verified_only:
        for n in sorted(set(verified)):
            print(n)
        return 0
    print('\n%s: probed %d live state pnames, %d verified, %d size mismatches\n'
          % (suite, probed, len(verified), len(mismatches)))
    for kindword, name, value, want, ts in sorted(mismatches, key=lambda r: r[1]):
        print('  %s csv=%-7s true=%-3d  %s (%s)'
              % (kindword, want, ts, name, value))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
