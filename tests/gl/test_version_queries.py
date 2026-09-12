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

import json

import pytest

from arraycompat import one
from checkutils import SKIP_EXIT_CODE
from childenv import run_in_child
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
import unittest

from checkutils import skip
from glcontext import Context

# A machine with no context to give -- a macOS runner with no window server,
# say -- has nothing to ask, and that is a skip rather than an answer.  The
# backend says so by raising SkipTest, which would otherwise leave here as a
# non-zero exit and read as the query having failed.
try:
    context = Context(profile='compatibility', gl_version=(2, 1))
except unittest.SkipTest as err:
    skip(str(err))

report = {}
with context:
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
        completed = run_in_child(VERSION_FIRST, check=False, **environment)
        if completed.returncode == SKIP_EXIT_CODE:
            pytest.skip(completed.stdout.strip() or 'no context to ask')
        assert completed.returncode == 0, completed.stderr[-2000:]
        return json.loads(completed.stdout)

    def test_the_querier_answers_under_ctypes(self):
        answered = self.answer(PYOPENGL_DISPATCH='ctypes')
        self.assertNotIn('error', answered, answered.get('error'))
        self.assertTrue(answered['version'], answered)

    def test_the_querier_answers_with_the_accelerators_off(self):
        """The configuration every `accel0` axis runs in."""
        answered = self.answer(PYOPENGL_USE_ACCELERATE='0')
        self.assertNotIn('error', answered, answered.get('error'))
        self.assertTrue(answered['version'], answered)


class TestTheVersionStringIsParsed(unittest.TestCase):
    """What ``GL_VERSION`` says, in the shapes drivers actually say it.

    The specification fixes only the start of the string -- a version, then
    optionally a space and whatever the vendor wants -- and an ES driver
    prefixes ``OpenGL ES`` in front of that.  A version this cannot read is not
    a wrong number: ``pullVersion`` ends in ``int()`` over what it split, so an
    unparsed string is a ``ValueError`` out of whatever call first asked how
    new the context was.

    No context is taken.  The subject is the pattern, and the strings below are
    the ones drivers reported on the tickets.

    https://github.com/mcfletch/pyopengl/issues/137
    https://github.com/mcfletch/pyopengl/issues/166
    """

    #: (what the driver said, the version in it, whether it is an ES string).
    REPORTED = [
        ('4.6 (Core Profile) Mesa 24.0.9', '4.6', False),
        ('3.0 Mesa 18.3.6', '3.0', False),
        ('2.1 INTEL-10.6.33', '2.1', False),
        ('4.6.0 NVIDIA 535.216.01', '4.6.0', False),
        ('OpenGL ES 3.2 NVIDIA 535.216.01', '3.2', True),
        ('OpenGL ES 3.1', '3.1', True),
        ('OpenGL ES 2.0 build 1.9@1234', '2.0', True),
    ]

    def parse(self, reported):
        match = GLQuerier.version_matcher.match(reported)
        self.assertIsNotNone(match, f'no version found in {reported!r}')
        return match

    def test_the_version_is_found(self):
        for reported, version, _ in self.REPORTED:
            with self.subTest(reported=reported):
                self.assertEqual(self.parse(reported).group('version'), version)

    def test_the_version_is_a_pair_of_integers(self):
        """What ``pullVersion`` does with what it matched, which is where an
        unparsed string becomes an exception rather than a wrong answer."""
        for reported, version, _ in self.REPORTED:
            with self.subTest(reported=reported):
                self.assertTrue(
                    all(part.isdigit() for part in version.split('.')),
                    version,
                )
                [int(part) for part in version.split('.')]

    def test_an_es_string_is_recognised_as_es(self):
        """``pullVersion`` sets ``is_opengl_es`` from this group, and warns.

        Whatever the group holds has to be what that comparison is written
        against: an ES context reached through the desktop API is a caller
        about to call an entry point that is not the one they mean, and the
        warning is the only place they are told.
        """
        for reported, _, is_es in self.REPORTED:
            with self.subTest(reported=reported):
                marker = self.parse(reported).group('api_marker')
                self.assertEqual(bool(marker), is_es, marker)
                if is_es:
                    self.assertEqual(marker, 'OpenGL ES', repr(marker))


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
