"""Opt-in native Windows ARM64 test (not collected by pytest).

Requires numpy, native glfw, and source-built ARM64 FreeGLUT/GLE installed
as freeglutarm64.vc14.dll and glearm64.vc14.dll in the bundled DLL directory.
Run from the checkout: python tests/checks/check_windows_arm64_dlls.py.
The DLLs are not supplied by this test or by the base PyOpenGL wheel.
"""
import pathlib
import struct
import sys
import sysconfig
from OpenGL import GL, GLUT, GLE, platform

def machine(path):
    with open(path, 'rb') as f:
        f.seek(0x3c)
        offset = struct.unpack('<I', f.read(4))[0]
        f.seek(offset)
        assert f.read(4) == b'PE\0\0'
        return struct.unpack('<H', f.read(2))[0]

assert sysconfig.get_platform() == 'win-arm64'
assert machine(sys.executable) == 0xaa64
for library in (platform.PLATFORM.GLUT, platform.PLATFORM.GLE):
    assert library is not None, 'Optional DLL failed to load'
    assert machine(library._name) == 0xaa64, library._name
    print('native library', pathlib.Path(library._name).name, hex(machine(library._name)))


def exercise():
    GL.glViewport(0, 0, 64, 64)
    for color, expected in [((1, 0, 0, 1), [255, 0, 0]), ((0, 1, 0, 1), [0, 255, 0])]:
        GL.glClearColor(*color)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glFinish()
        pixel = GL.glReadPixels(32, 32, 1, 1, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
        assert bytes(pixel)[:3] == bytes(expected), repr(pixel)
    GLE.gleSetNumSides(24)
    assert GLE.gleGetNumSides() == 24
    style = GLE.gleGetJoinStyle()
    GLE.gleSetJoinStyle(GLE.TUBE_JN_ANGLE | GLE.TUBE_NORM_FACET)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-1, 1, -1, 1, -2, 2)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glClearColor(0, 0, 0, 1)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1, 0, 0)
    GLE.glePolyCylinder([[-1, 0, 0], [-.7, 0, 0], [.7, 0, 0], [1, 0, 0]], None, .25)
    GL.glFinish()
    pixel = GL.glReadPixels(32, 32, 1, 1, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
    assert bytes(pixel)[:3] == bytes([255, 0, 0]), repr(pixel)
    assert GL.glGetError() == GL.GL_NO_ERROR
    GLE.gleSetJoinStyle(style)

import glfw
assert glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(64, 64, 'native smoke', None, None)
assert window
glfw.make_context_current(window)
exercise()
print('GLFW context: two-color readback + GLE geometry PASS')
glfw.destroy_window(window)
glfw.terminate()

GLUT.glutInit(['native-smoke'])
GLUT.glutInitDisplayMode(GLUT.GLUT_SINGLE | GLUT.GLUT_RGB)
GLUT.glutInitWindowSize(64, 64)
window = GLUT.glutCreateWindow(b'native smoke')
assert window > 0
exercise()
GLUT.glutDestroyWindow(window)
print('FreeGLUT context: two-color readback + GLE geometry PASS')
