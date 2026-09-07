"""An arming the ctypes implementation could not attribute to a context.

The compiled layer knows which context is current and records what it armed
against that handle.  The ctypes implementation holds one binding for the
process and knows only what the program told :func:`make_current`; until it is
told anything, the context it arms debug output in is recorded under 0, which
means "we were not told" rather than naming anything.

So 0 stops describing the current context the moment the program says the
situation has changed -- a context destroyed, or another one made current.  A
check still reading the flag then reads one the current context's driver never
sets, which is a check that passes everything.  These hold the layer to giving
that arming up, so the next context is offered the mechanism afresh.
"""

import pytest

dispatch = pytest.importorskip('OpenGL.dispatch')


@pytest.fixture
def ctypes_armed(monkeypatch):
    """The ctypes implementation, armed against a context nothing named."""
    stops = []
    monkeypatch.setattr(dispatch, '_layer', lambda: None)
    monkeypatch.setattr(dispatch, '_installed_callbacks', {0: object()})
    monkeypatch.setattr(dispatch, '_offered', {0})
    monkeypatch.setattr(dispatch, '_ctypes_current_context', 0)
    monkeypatch.setattr(dispatch, '_stop_reading_debug_output',
                        lambda: stops.append(0))
    # Nothing here has a context, and the offer that follows would make GL
    # calls into whatever is current.  What is under test is what happens to
    # the arming, so record the offer rather than making it.
    offers = []
    monkeypatch.setattr(dispatch, 'offer_debug_output',
                        lambda: offers.append(dispatch._context_key()))
    monkeypatch.setattr(dispatch, '_end_suspended_block', lambda: None)
    return stops, offers


class TestForgettingAContextGivesTheArmingUp:
    def test_the_flag_stops_being_read(self, ctypes_armed):
        stops, _ = ctypes_armed
        dispatch.forget_context(0x1234)
        assert stops == [0]

    def test_and_the_next_context_is_offered_again(self, ctypes_armed):
        dispatch.forget_context(0x1234)
        assert 0 not in dispatch._offered
        assert 0 not in dispatch._installed_callbacks


class TestNamingAContextGivesTheArmingUp:
    """``make_current`` is the program saying which context it is on now; the
    arming recorded against "we were not told" cannot be that one."""

    def test_the_flag_stops_being_read(self, ctypes_armed):
        stops, _ = ctypes_armed
        dispatch.make_current(0x1234)
        assert stops == [0]

    def test_and_the_named_context_is_the_one_offered(self, ctypes_armed):
        _, offers = ctypes_armed
        dispatch.make_current(0x1234)
        assert offers == [0x1234]


class TestTheCompiledLayerKeepsItsOwn:
    """It records against the handle the layer itself read, so 0 there is a
    context that genuinely had none to give -- not an absence of information."""

    def test_forgetting_another_context_leaves_it_alone(self, monkeypatch):
        stops = []

        class Layer:
            """Enough of the compiled layer for what forget_context calls."""

            def forget_context(self, handle):
                pass

        monkeypatch.setattr(dispatch, '_layer', lambda: Layer())
        monkeypatch.setattr(dispatch, '_installed_callbacks', {0: object()})
        monkeypatch.setattr(dispatch, '_offered', {0})
        monkeypatch.setattr(dispatch, '_stop_reading_debug_output',
                            lambda: stops.append(0))
        monkeypatch.setattr(dispatch, '_end_suspended_block', lambda: None)
        monkeypatch.setattr(dispatch, '_context_key', lambda: 0x1234)
        monkeypatch.setattr(dispatch, 'offer_debug_output', lambda: None)
        dispatch.forget_context(0x5678)
        assert stops == []
        assert 0 in dispatch._installed_callbacks
