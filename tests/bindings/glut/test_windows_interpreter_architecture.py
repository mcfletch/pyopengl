"""Windows DLL names must follow the Python ABI, not the host CPU."""
import sys
import sysconfig
import unittest
from unittest.mock import patch

@unittest.skipUnless(sys.platform == 'win32', 'Windows loader')
class InterpreterArchitectureTests(unittest.TestCase):
    def test_interpreter_architecture_not_host_or_pointer_size(self):
        from OpenGL.platform import win32
        for target, expected in [('win-arm64', 'arm64'), ('win-amd64', '64'), ('win32', '32')]:
            with self.subTest(target=target), patch.object(sysconfig, 'get_platform', return_value=target):
                self.assertEqual(win32._size(), expected)

    def test_native_arm64_names(self):
        if sysconfig.get_platform() != 'win-arm64':
            self.skipTest('Requires native ARM64 interpreter')
        from OpenGL.platform import win32
        self.assertEqual(win32.size, 'arm64')
        self.assertIn('freeglutarm64.vc14', win32.Win32Platform.GLUT_LIBRARY_NAMES)
        self.assertNotIn('freeglut64.vc14', win32.Win32Platform.GLUT_LIBRARY_NAMES)

if __name__ == '__main__':
    unittest.main()
