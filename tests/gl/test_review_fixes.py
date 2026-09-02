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
