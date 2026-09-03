#! /usr/bin/env python3
"""GLU string / error / extension queries: gluGetString, gluErrorString,
gluCheckExtension."""

import unittest

from glutestcase import GLUTestCase, requireEntryPoint
from OpenGL.GLU import *
from OpenGL.GLU import GLU_VERSION, GLU_EXTENSIONS


class TestGLUStrings(GLUTestCase):
    def test_get_string_version(self):
        version = gluGetString(GLU_VERSION)
        self.assertTrue(version, 'gluGetString(GLU_VERSION) returned empty')
        text = version.decode('ascii') if isinstance(version, bytes) else version
        # GLU advertises a dotted version such as "1.3".
        self.assertRegex(text, r'^\d+\.\d+')

    def test_get_string_extensions(self):
        ext = gluGetString(GLU_EXTENSIONS)
        # May be empty on some libraries, but the call must succeed and return
        # either bytes/str (never raise).
        self.assertIsNotNone(ext)
        self.check_error('gluGetString(GLU_EXTENSIONS)')

    def test_error_string(self):
        # gluErrorString must map a GLU error enum to a human-readable message.
        message = gluErrorString(GLU_INVALID_ENUM)
        self.assertTrue(message)
        text = message.decode('ascii') if isinstance(message, bytes) else message
        self.assertIsInstance(text, str)

    def test_error_string_gl_enum(self):
        # GLU also stringifies the base GL error enums.
        from OpenGL.GL import GL_INVALID_VALUE

        self.assertTrue(gluErrorString(GL_INVALID_VALUE))

    def test_check_extension_present(self):
        requireEntryPoint(gluCheckExtension, 'gluCheckExtension')
        ext = gluGetString(GLU_EXTENSIONS) or b''
        names = (ext.decode('ascii') if isinstance(ext, bytes) else ext).split()
        if not names:
            self.skipTest('no GLU extensions advertised to probe')
        present = names[0].encode('ascii')
        self.assertTrue(gluCheckExtension(present, ext))

    def test_check_extension_absent(self):
        requireEntryPoint(gluCheckExtension, 'gluCheckExtension')
        ext = gluGetString(GLU_EXTENSIONS) or b''
        # A name that cannot be in the list must report False, not error.
        self.assertFalse(gluCheckExtension(b'GLU_not_a_real_extension', ext))
        self.check_error('gluCheckExtension')


if __name__ == '__main__':
    unittest.main()
