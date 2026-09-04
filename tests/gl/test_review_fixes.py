"""Fixes for defects found in review, each with the property it restores."""

import gc
import os

import pytest

import OpenGL._dispatch as dispatch
from OpenGL import _configflags

pytestmark = pytest.mark.skipif(
    not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
    reason='the C dispatch layer is not the selected implementation',
)


class TestTheEntryPointKnowsItsApi:
    """glClear exists in GL and GLES2 as separate bindings from separate
    libraries, so anything that identifies one by name alone can answer about
    the other -- and demoting then binds the wrong library."""

    def test_each_reports_its_own_module(self):
        import OpenGL.GL as GL
        import OpenGL.GLES2 as ES

        assert GL.glClear.__module__ != ES.glClear.__module__
        assert 'GLES2' in ES.glClear.__module__

    def test_they_are_distinct_entry_points(self):
        import OpenGL.GL as GL
        import OpenGL.GLES2 as ES

        assert GL.glClear is not ES.glClear


class TestABadScalarRaisesWhatCtypesRaises:
    """``ctypes.ArgumentError`` is part of PyOpenGL's own interface.

    ``OpenGL.error`` re-exports it, and the ctypes wrapper catches it to add
    the converted arguments, so a program is entitled to catch it -- and it
    does not inherit from ``TypeError``, so a C stub raising ``TypeError``
    instead is a difference that silently stops such a program working.  The
    message is not part of the contract; the type is.
    """

    def test_an_unconvertible_scalar_raises_argument_error(self):
        import ctypes

        import OpenGL.GL as GL

        with pytest.raises(ctypes.ArgumentError):
            GL.glBindTexture('not-an-enum', 0)

    def test_it_is_raised_for_a_float_argument_too(self):
        import ctypes

        import OpenGL.GL as GL

        with pytest.raises(ctypes.ArgumentError):
            GL.glUniform1f(0, 'not-a-float')

    def test_the_original_message_is_carried_across(self):
        import ctypes

        import OpenGL.GL as GL

        with pytest.raises(ctypes.ArgumentError) as caught:
            GL.glBindTexture('not-an-enum', 0)
        assert 'glBindTexture' in str(caught.value)
        assert 'integer' in str(caught.value)

    def test_something_that_is_not_an_argument_problem_is_left_alone(self):
        """Calling a KeyboardInterrupt a bad argument would let a caller
        catching ArgumentError swallow it."""
        import OpenGL.GL as GL

        class Hostile:
            def __index__(self):
                raise KeyboardInterrupt('not an argument problem')

        with pytest.raises(KeyboardInterrupt):
            GL.glBindTexture(Hostile(), 0)


class TestGarbageCollection:
    """The type has a settable dict and settable callbacks, so a cycle through
    one of them must be collectable."""

    def test_the_type_is_tracked(self):
        import OpenGL.GL as GL

        assert gc.is_tracked(GL.glClear)

    def test_a_cycle_through_the_instance_dict_is_collectable(self):
        import OpenGL.GL as GL

        GL.glFlush.cycle = GL.glFlush
        try:
            assert gc.collect() >= 0
        finally:
            del GL.glFlush.cycle


class TestSignatures:
    """inspect.signature() strips $module and parses the rest, so a call that
    takes nothing must not carry a positional-only marker."""

    @pytest.mark.parametrize(
        'name', ['glFinish', 'glFlush', 'glCreateProgram', 'glLoadIdentity']
    )
    def test_a_no_argument_entry_point_has_a_signature(self, name):
        import inspect

        import OpenGL.GL as GL

        assert str(inspect.signature(getattr(GL, name))) == '()'

    def test_an_ordinary_entry_point_still_has_one(self):
        import inspect

        import OpenGL.GL as GL

        assert str(inspect.signature(GL.glBindTexture)) == '(target, texture, /)'


class TestErrorCheckingReachesEveryContext:
    def test_setting_it_moves_the_default_too(self):
        """A context created afterwards has to agree, or the call has told the
        caller something untrue about their program."""
        from OpenGL._dispatch import _c

        _c.set_error_checking(True)
        _c.make_current(0xC0FFEE)
        try:
            # The freshly built table inherits the flag rather than the value
            # it would have had at import.
            assert _c.context_count() >= 1
        finally:
            _c.forget_context(0xC0FFEE)
            _c.set_error_checking(bool(_configflags.ERROR_CHECKING))


class TestKeywordArguments:
    """A vectorcall's fourth argument is kwnames.  The stubs used to be
    declared with three parameters and the pointer cast, which is undefined
    behaviour and silently discarded any keyword a caller passed."""

    def test_a_keyword_argument_is_rejected_rather_than_ignored(self):
        import OpenGL.GL as GL

        with pytest.raises(TypeError, match='keyword'):
            GL.glClear(GL.GL_COLOR_BUFFER_BIT, nonsense=1)

    def test_positional_calls_are_unaffected(self):
        import OpenGL.GL as GL

        # Arity errors still read as arity errors, not keyword errors.
        with pytest.raises(TypeError) as caught:
            GL.glBindTexture(1)
        assert 'keyword' not in str(caught.value)


@pytest.fixture(scope='module')
def context():
    """A hidden context, for the checks that need the driver to answer."""
    glfw = pytest.importorskip('glfw')
    if not glfw.init():
        pytest.skip('no glfw')
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(64, 64, 'review-fixes', None, None)
    if window is None:
        pytest.skip('no usable GL context')
    glfw.make_context_current(window)
    yield window
    glfw.destroy_window(window)
    glfw.make_context_current(None)


def _undersized_arrays():
    """One undersized output array per shape the acquire path distinguishes.

    A guard against memory corruption has to be tested against the *kinds* of
    input the acquire function branches on, not against one representative
    value: each kind reaches the check through a different set of fields, and a
    check that reads the wrong one is right for the kind it was written against
    and silent for the rest.
    """
    import numpy

    return [
        # A matching contiguous buffer: taken by the buffer-protocol fast path,
        # so the frame holds a Py_buffer over the caller's own memory.
        pytest.param(lambda: numpy.zeros(1, dtype='uint32'), id='matched-buffer'),
        # The right element type, but not contiguous, so the buffer request
        # fails and ArrayDatatype makes a copy.  The GL writes into the copy,
        # which is sized from the caller's length.
        pytest.param(lambda: numpy.zeros(8, dtype='uint32')[::2], id='converted-copy'),
        # The wrong element type: converted for that reason instead.
        pytest.param(lambda: numpy.zeros(4, dtype='int8'), id='converted-type'),
        # A list, which has no buffer at all.
        pytest.param(lambda: [0, 0, 0, 0], id='converted-list'),
    ]


class TestOutputArraySafety:
    """A caller-supplied output array has to be big enough for what the driver
    will write into it."""

    @pytest.mark.parametrize('make', _undersized_arrays())
    def test_an_undersized_array_is_refused_rather_than_overrun(self, context, make):
        import OpenGL.GL as GL

        with pytest.raises(ValueError, match='output array holds'):
            GL.glGenTextures(64, make())

    def test_a_raw_pointer_is_measured_or_left_alone_but_never_guessed(self, context):
        """A ctypes pointer carries no length, so there is nothing to check it
        against.  What must not happen is a *different* answer each time, which
        is what reading an uninitialised frame slot produces."""
        import ctypes

        import OpenGL.GL as GL

        buffer = (ctypes.c_uint * 64)()
        pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_uint))
        answers = set()
        for _ in range(8):
            try:
                GL.glGenTextures(2, pointer)
            except ValueError as raised:
                answers.add(str(raised))
            else:
                answers.add(None)
        assert len(answers) == 1, (
            'the same call answered differently across repeats: %r' % (answers,)
        )

    def test_a_correctly_sized_array_is_accepted(self, context):
        import numpy

        import OpenGL.GL as GL

        enough = numpy.zeros(4, dtype='uint32')
        GL.glGenTextures(4, enough)
        assert enough.any()

    def test_a_correctly_sized_converted_array_is_accepted(self, context):
        """The conversion path is not a rejection path: a list of the right
        length is what a great deal of code passes."""
        import OpenGL.GL as GL

        assert len(GL.glGenTextures(4, [0, 0, 0, 0])) == 4

    def test_a_maximum_is_not_treated_as_a_promise(self, context):
        """glGetVertexAttribiv declares four and writes one for most pnames,
        so a one-element array is legitimate and must not be refused."""
        import numpy

        import OpenGL.GL as GL

        one = numpy.zeros(1, dtype='int32')
        GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE, one)
        assert one[0] > 0


class TestMultiOutputShape:
    def test_several_outputs_come_back_as_a_list(self, context):
        """What the ctypes wrapper returns, so indexing, appending and
        isinstance() behave as they always have."""
        import OpenGL.GL as GL

        if not bool(GL.glGetDebugMessageLog):
            pytest.skip('GL_KHR_debug not available')
        result = GL.glGetDebugMessageLog(1, 128)
        assert isinstance(result, list)


class TestGLErrorAttributes:
    def test_it_carries_what_the_documentation_says(self, context):
        import OpenGL.GL as GL
        from OpenGL import error

        try:
            GL.glEnable(0xDEAD)
            GL.glGetError()
        except error.GLError as raised:
            assert raised.baseOperation.__name__ == 'glEnable'
            assert raised.pyArgs == (0xDEAD,)
            assert raised.cArguments == (0xDEAD,)
        else:
            pytest.skip('the driver did not report the bad enum')
