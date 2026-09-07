#! /usr/bin/env python3
"""What the library believes about the context, against what the context says.

``OpenGL.extensions`` decides whether an entry point exists by asking a querier
about the version and the extension list, and the answer gates every
version-guarded binding in the package.  So the querier's opinion has to match
what ``glGetString`` reports -- a querier that reads the version one way and
the driver another silences functions the context provides, or exposes ones it
does not.

``_lookupint.LookupInt`` is the other direction: a constant whose value is not
known until there is a context, deferred until something asks for it.
"""

import unittest

from arraycompat import one
from childenv import json_from_child
from gltestcase import GLTestCase
from OpenGL.extensions import GLQuerier, hasGLExtension
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.raw.GL import _lookupint


class TestTheContextIdentifiesItself(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_the_extension_string_is_not_empty(self):
        self.assertTrue(glGetString(GL_EXTENSIONS))

    def test_the_querier_and_the_driver_agree_about_the_version(self):
        """``GLQuerier.pullVersion()`` is what gates the version bindings."""
        pulled = tuple(GLQuerier.pullVersion()[:2])
        reported = self.version()
        self.assertEqual(
            pulled, reported,
            'the querier reads GL %r where glGetString reports %r'
            % (pulled, reported),
        )

    def test_the_2_0_entry_points_follow_the_2_0_answer(self):
        """A version the querier claims has to bring its functions with it."""
        if hasGLExtension('GL_VERSION_GL_2_0'):
            self.assertTrue(glShaderSource)
            self.assertTrue(glUniform1f)
        else:
            self.assertFalse(glShaderSource)
            self.assertFalse(glUniform1f)


#: Ask the querier for the version and nothing else, in a fresh process.  The
#: order is the point: ``pullExtensions`` sets the raw ``glGetString``'s restype
#: to the string it returns, and that is a lasting change to a shared entry
#: point -- so a process that has pulled the extensions first cannot show
#: whether ``pullVersion`` can stand on its own.
VERSION_FIRST = r'''
import json
import os

os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')

report = {}
from glcontext import Context

with Context(profile='compatibility', gl_version=(2, 1)):
    from OpenGL.extensions import GLQuerier

    try:
        report['version'] = GLQuerier.pullVersion()
    except Exception as err:
        report['error'] = '%s: %s' % (type(err).__name__, err)
print(json.dumps(report))
'''


class TestTheVersionIsReadableOnItsOwn(unittest.TestCase):
    """``pullVersion`` must not need ``pullExtensions`` to have run first.

    The two read the same raw entry point, whose declared return is an array
    type: only the C dispatch layer turns that into the string it is, so under
    ctypes the version read answers with an array. That was invisible for as
    long as the extensions were always pulled first, since pulling them sets
    the restype for whatever runs afterwards.
    """

    def answer(self, **environment):
        return json_from_child(VERSION_FIRST, **environment)

    def test_the_querier_answers_under_ctypes(self):
        answered = self.answer(PYOPENGL_DISPATCH='ctypes')
        self.assertNotIn('error', answered, answered.get('error'))
        self.assertTrue(answered['version'], answered)

    def test_the_querier_answers_with_the_accelerators_off(self):
        """The configuration every `accel0` axis runs in."""
        answered = self.answer(PYOPENGL_USE_ACCELERATE='0')
        self.assertNotIn('error', answered, answered.get('error'))
        self.assertTrue(answered['version'], answered)


class TestAConstantResolvedAgainstTheContext(GLTestCase):
    """``LookupInt`` defers a glGet until something reads the value."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_it_reads_the_value_the_driver_reports(self):
        deferred = _lookupint.LookupInt(GL_NUM_COMPRESSED_TEXTURE_FORMATS, GLint)
        direct = one(glGetIntegerv(GL_NUM_COMPRESSED_TEXTURE_FORMATS))
        self.assertEqual(int(deferred), direct)
        self.check_error('GL_NUM_COMPRESSED_TEXTURE_FORMATS')

    def test_it_reads_it_again_rather_than_caching_the_first_context(self):
        """The value belongs to a context, and a process outlives contexts."""
        deferred = _lookupint.LookupInt(GL_MAX_TEXTURE_SIZE, GLint)
        first = int(deferred)
        self.assertEqual(first, int(deferred))
        self.assertTrue(first, 'GL_MAX_TEXTURE_SIZE read as zero')


class TestTheFramebufferBindingQuery(GLTestCase):
    profile = 'compatibility'
    gl_version = (3, 0)

    def test_the_read_binding_is_readable(self):
        """``GL_READ_FRAMEBUFFER_BINDING`` arrived with GL 3.0."""
        self.require_version(3, 0)
        binding = glGetInteger(GL_READ_FRAMEBUFFER_BINDING)
        self.assertEqual(one(binding), int(self.draw_framebuffer()))
        self.check_error('GL_READ_FRAMEBUFFER_BINDING')


if __name__ == '__main__':
    unittest.main()
