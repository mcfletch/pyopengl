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


class TestNothingIsOfferedWhereThereIsNoContext:
    """Arming debug output is GL calls -- ``glEnable``,
    ``glDebugMessageCallback`` -- so it needs a context current.

    Whether the layer has a *name* for that context is a different question. An
    entry point is resolved before a context exists and after one has gone -- a
    probe for what a platform offers, a cleanup handler running past the window
    -- and each of those resolutions makes the offer. The ctypes implementation
    has only what ``make_current`` was told, which stops being true the moment
    the context goes, so a handle on record is not evidence that anything is
    current now.
    """

    @pytest.fixture
    def offering(self, monkeypatch):
        """A record of what the offer armed, with nothing calling GL."""
        armed = []
        monkeypatch.setattr(dispatch, '_offered', set())
        monkeypatch.setattr(dispatch, '_layer', lambda: None)
        monkeypatch.setattr(dispatch, '_debug_output_wanted', lambda: True)
        monkeypatch.setattr(dispatch, 'use_debug_output', armed.append)
        return armed

    def test_a_named_context_that_has_gone_is_not_armed(
        self, offering, monkeypatch
    ):
        monkeypatch.setattr(dispatch, '_context_key', lambda: 0x1234)
        monkeypatch.setattr(dispatch, '_has_current_context', lambda: False)
        dispatch.offer_debug_output()
        assert offering == []

    def test_nor_is_one_nothing_has_named(self, offering, monkeypatch):
        monkeypatch.setattr(dispatch, '_context_key', lambda: 0)
        monkeypatch.setattr(dispatch, '_has_current_context', lambda: False)
        dispatch.offer_debug_output()
        assert offering == []

    def test_and_a_context_that_is_there_is_offered(self, offering, monkeypatch):
        monkeypatch.setattr(dispatch, '_context_key', lambda: 0x1234)
        monkeypatch.setattr(dispatch, '_has_current_context', lambda: True)
        dispatch.offer_debug_output()
        assert offering == [True]


class TestForgettingAContextAsksWhetherThereIsOneToAsk:
    """Giving the callback back is a GL call, so it needs a context to make it
    in, and ``forget_context`` is documented for a context that has been
    destroyed.  What the layer was *last told* cannot answer that -- a context
    destroyed without a ``make_current`` after it is still the one on record --
    so the driver is asked which context is current, and where that is not this
    one nothing is called into it.
    """

    @pytest.fixture
    def given_back(self, monkeypatch):
        """A record of whether the callback was handed back, and to whom."""
        handed = []
        monkeypatch.setattr(dispatch, '_installed_callbacks', {1: object()})
        monkeypatch.setattr(dispatch, '_layer', lambda: None)
        monkeypatch.setattr(dispatch, 'use_debug_output', handed.append)
        return handed

    def test_a_context_that_is_still_current_hands_its_callback_back(
        self, given_back, monkeypatch
    ):
        monkeypatch.setattr(dispatch, '_current_context', lambda: 1)
        dispatch.forget_context(1)
        assert given_back == [False]

    def test_a_context_that_has_already_gone_is_not_called_into(
        self, given_back, monkeypatch
    ):
        """The driver drops the callback with the context in any case, and a
        GL call with nothing current is an error on Windows rather than the
        quiet no-op it is elsewhere."""
        monkeypatch.setattr(dispatch, '_current_context', lambda: 0)
        dispatch.forget_context(1)
        assert given_back == []
        assert 1 not in dispatch._installed_callbacks, 'forgotten regardless'

    def test_nor_is_a_context_that_another_has_replaced(
        self, given_back, monkeypatch
    ):
        monkeypatch.setattr(dispatch, '_current_context', lambda: 2)
        dispatch.forget_context(1)
        assert given_back == []

    def test_the_current_context_is_the_one_the_driver_names(self):
        """Read from the platform each time, since that is the only source that
        knows a context has been destroyed."""
        from OpenGL import platform

        getter = getattr(platform.PLATFORM, 'GetCurrentContext', None)
        if getter is None:                  # pragma: no cover - has one here
            pytest.skip('this platform cannot say which context is current')
        assert dispatch._current_context() == int(getter() or 0)
