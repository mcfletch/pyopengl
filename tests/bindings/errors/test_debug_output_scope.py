"""Switching driver debug output off in one context leaves the others alone.

``use_debug_output`` installs a driver callback per context and points the
error check at the flag that callback sets. Where that pointing is recorded
decides who else a context switching off can affect.

The compiled layer keeps the mode with the context's dispatch table, so a
context hands its own back and no other context is party to it. The ctypes
implementation holds a single checker for the process, so its reader may only
go back to a ``glGetError`` per call once the last context has given its
callback up -- otherwise disabling in one context stops the other from using
the mechanism it still has installed, and "undoes what switching it on did"
undoes rather more than that.

Nothing is answered wrongly either way: both mechanisms find the same errors.
What is at stake is the cost the switch exists to avoid.
"""

import pytest

dispatch = pytest.importorskip('OpenGL.dispatch')


@pytest.fixture
def released(monkeypatch):
    """A callback registry of this test's own, and a record of what stopped.

    Both implementations are driven through :func:`_stop_reading_debug_output`,
    which is the one thing a release can decide to do or not do, so the record
    is the same shape for either.
    """
    stops = []
    monkeypatch.setattr(dispatch, '_installed_callbacks', {})
    monkeypatch.setattr(dispatch, '_stop_reading_debug_output',
                        lambda: stops.append(0))
    return stops


@pytest.fixture
def compiled(monkeypatch, released):
    """As ``released``, with the compiled layer reported as the one in use."""
    monkeypatch.setattr(dispatch, '_layer', lambda: object())
    return released


@pytest.fixture
def ctypes_only(monkeypatch, released):
    """As ``released``, with the ctypes implementation reported as in use."""
    monkeypatch.setattr(dispatch, '_layer', lambda: None)
    return released


class TestTheCompiledLayerAnswersPerContext:
    """The mode is a field of the context's dispatch table, so releasing one
    context's callback is that context's business and nobody else's."""

    def test_disabling_the_only_one_stops_reading(self, compiled):
        dispatch._installed_callbacks[1] = object()
        dispatch._release_debug_callback(1)
        assert compiled == [0]

    def test_disabling_one_of_two_still_stops_reading(self, compiled):
        """The other context keeps its own mode, in its own table."""
        dispatch._installed_callbacks[1] = object()
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        assert compiled == [0]


class TestCtypesWaitsForTheLastOneOut:
    """One checker for the process, so the reader is shared and may only go
    back when nothing holds a callback any more."""

    def test_disabling_the_only_one_stops_reading(self, ctypes_only):
        dispatch._installed_callbacks[1] = object()
        dispatch._release_debug_callback(1)
        assert ctypes_only == [0]

    def test_disabling_one_of_two_leaves_the_reader_alone(self, ctypes_only):
        """The other context still has its callback and its driver-side debug
        output; taking the reader away would leave it paying for both and
        using neither."""
        dispatch._installed_callbacks[1] = object()
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        assert ctypes_only == []

    def test_and_the_last_one_out_stops_it(self, ctypes_only):
        dispatch._installed_callbacks[1] = object()
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        dispatch._release_debug_callback(2)
        assert ctypes_only == [0]

    def test_disabling_a_context_that_never_had_one_is_quiet(self, ctypes_only):
        """It holds no callback, so there is nothing of its to give back."""
        dispatch._installed_callbacks[2] = object()
        dispatch._release_debug_callback(1)
        assert ctypes_only == []


class TestReleasingReportsWhetherThereWasOne:
    def test_the_first_release_reports_one_and_the_second_none(self, ctypes_only):
        dispatch._installed_callbacks[1] = object()
        assert dispatch._release_debug_callback(1) is True
        assert dispatch._release_debug_callback(1) is False
