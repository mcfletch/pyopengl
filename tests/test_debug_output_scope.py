"""Switching driver debug output off in one context leaves the others alone.

``use_debug_output`` installs a driver callback per context and puts the whole
process into the error mode that reads the flag that callback sets. The
callback is per context; the mode is not. So the mode may only go back to
per-call ``glGetError`` once the last context has given its callback up --
otherwise disabling in one context stops the other from using the mechanism it
still has installed, and the docstring's "undoes what switching it on did"
undoes rather more than that.

Nothing is answered wrongly either way: both mechanisms find the same errors.
What is at stake is the cost the switch exists to avoid.
"""

import pytest

dispatch = pytest.importorskip('OpenGL._dispatch')

if not dispatch.AVAILABLE:
    # The accounting lives in the compiled layer's switch; with no extension
    # there is no error mode to hand back.
    pytest.skip('the C dispatch extension is not built',
                allow_module_level=True)


@pytest.fixture
def registry(monkeypatch):
    """A callback registry of this test's own, and a record of mode changes."""
    modes = []
    monkeypatch.setattr(dispatch, '_installed_callbacks', {})
    monkeypatch.setattr(dispatch._c, 'set_error_mode', modes.append,
                        raising=False)
    return modes


class TestTheModeFollowsTheLastCallback:
    """Driven through the bookkeeping rather than through two live contexts:
    what is under test is the accounting, and a second context on a headless
    runner is a fixture problem, not this question."""

    def test_disabling_the_only_one_returns_the_mode(self, registry):
        dispatch._installed_callbacks[1] = object()
        dispatch._release_debug_callback(1)
        assert registry == [0]

    def test_disabling_one_of_two_leaves_the_mode_alone(self, registry):
        """The other context still has its callback and its driver-side debug
        output; taking the mode away would leave it paying for both and using
        neither."""
        dispatch._installed_callbacks[1] = object()
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        assert registry == []

    def test_and_the_last_one_out_returns_it(self, registry):
        dispatch._installed_callbacks[1] = object()
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        dispatch._release_debug_callback(2)
        assert registry == [0]

    def test_disabling_a_context_that_never_had_one_is_quiet(self, registry):
        """It holds no callback, so there is nothing of its to give back."""
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        assert registry == []

    def test_releasing_reports_whether_there_was_one(self, registry):
        dispatch._installed_callbacks[1] = object()
        assert dispatch._release_debug_callback(1) is True
        assert dispatch._release_debug_callback(1) is False
