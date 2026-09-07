"""Two answers the suite's own fixtures depend on, checked without a context.

Both are places where the framework asks a question whose wrong answer is not a
failed assertion but a whole file of tests reporting something other than what
they test: a version query the context does not serve, and a window GLFW
refused reading as a window it made.
"""

import unittest

import glcontext
import pytest


class TestReadingTheVersion:
    """``GL_MAJOR_VERSION`` arrived with GL 3.0 and ES 3.0.

    Asking a 2.1 context for it is ``GL_INVALID_ENUM``, and macOS's legacy
    profile -- the only one with fixed function in it, so the only one the
    compatibility cases can run on -- is 2.1.  The version is in
    ``GL_VERSION``, which every context answers.
    """

    class FakeContext:
        """Enough of ContextTestCase for :meth:`version` to run."""

        version = glcontext.ContextTestCase.version

        def __init__(self, reported, integers=None):
            self.reported = reported
            self.integers = integers
            self.gl = self

        GL_VERSION = 0x1F02
        GL_MAJOR_VERSION = 0x821B
        GL_MINOR_VERSION = 0x821C

        def getString(self, enum):
            return self.reported

        def getInteger(self, enum, count=1):
            if self.integers is None:
                raise AssertionError(
                    'the version was asked for with a query this context does '
                    'not serve'
                )
            return self.integers[enum]

    def test_a_legacy_context_answers_from_its_version_string(self):
        assert self.FakeContext('2.1 ATI-7.12.9').version() == (2, 1)

    def test_so_does_a_modern_one(self):
        assert self.FakeContext('4.6 (Core Profile) Mesa 24.0').version() == (4, 6)

    def test_and_an_es_context(self):
        assert self.FakeContext('OpenGL ES 3.2 Mesa 24.0').version() == (3, 2)

    def test_a_string_nothing_can_read_falls_back_to_the_queries(self):
        """Which exist from GL 3.0 onwards, and answer for themselves."""
        context = self.FakeContext(
            'gibberish',
            {self.FakeContext.GL_MAJOR_VERSION: 4,
             self.FakeContext.GL_MINOR_VERSION: 1},
        )
        assert context.version() == (4, 1)


class TestWhetherGLFWMadeTheWindow:
    def test_a_window_glfw_refused_is_not_a_window(self):
        """The trap this exists for: the refusal is falsy but not None."""
        glfw = pytest.importorskip('glfw')
        refused = glfw._glfw.glfwCreateWindow.restype()
        assert refused is not None, 'the premise: a NULL window is not None'
        assert not glcontext.window_was_made(refused)

    def test_and_one_it_made_is(self):
        glfw = pytest.importorskip('glfw')
        made = glfw._glfw.glfwCreateWindow.restype.from_buffer_copy(
            (0x1234).to_bytes(8, 'little')
        )
        assert glcontext.window_was_made(made)

    def test_nothing_at_all_is_not_a_window_either(self):
        assert not glcontext.window_was_made(None)


class TestAskingWhetherTheContextHasIt:
    """``bool(some_entry_point)`` is a question about the library, not the
    context.  macOS exports every entry point from the framework whatever the
    current context implements, so a guard written against the symbol admits a
    2.1 context to a call that answers ``GL_INVALID_OPERATION`` -- reported
    against the call, after the guard has already decided it was there.
    """

    class FakeContext:
        require_feature = glcontext.ContextTestCase.require_feature

        def __init__(self, version, extensions):
            self._version = version
            self._extensions = set(extensions)

        def version(self):
            return self._version

        def extensions(self):
            return self._extensions

        def skipTest(self, reason):
            raise unittest.SkipTest(reason)

    def _ask(self, version, extensions):
        self.FakeContext(version, extensions).require_feature(
            'vertex array objects', (3, 0), 'GL_ARB_vertex_array_object'
        )

    def _expect_it_runs(self, version, extensions):
        """Assert no skip, as an assertion rather than by not raising.

        pytest turns a ``SkipTest`` raised inside a test into a skipped test,
        so a case that only calls ``_ask`` reports green whichever way the
        helper answers, and the half of this that says a context *has* the
        feature would never fail.
        """
        try:
            self._ask(version, extensions)
        except unittest.SkipTest as err:
            raise AssertionError(
                'skipped a context that has vertex array objects: %s' % (err,)
            ) from None

    def test_a_context_with_it_in_core_runs(self):
        self._expect_it_runs((3, 3), [])

    def test_and_the_version_that_introduced_it_counts(self):
        self._expect_it_runs((3, 0), [])

    def test_an_older_one_offering_the_extension_runs_too(self):
        self._expect_it_runs((2, 1), ['GL_ARB_vertex_array_object'])

    def test_an_older_one_without_it_skips(self):
        """macOS's legacy profile: 2.1, and the vendor extension instead."""
        with pytest.raises(unittest.SkipTest) as caught:
            self._ask((2, 1), ['GL_APPLE_vertex_array_object'])
        reason = str(caught.value)
        # what the context is, what would have been enough, and what it was
        # asked for -- a skip saying only that something was absent leaves the
        # reader to find out which of the three was the problem.
        assert '2.1' in reason and '3.0' in reason, reason
        assert 'GL_ARB_vertex_array_object' in reason, reason
        assert 'vertex array objects' in reason, reason
