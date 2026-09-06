"""Destroying a GLUT window lets go of its context data

The names stored against a window's context -- textures, buffers, arrays --
belong to a context that stops existing with the window, so they are dropped
first.  Whether that succeeds or not the window still has to be destroyed, so
:func:`OpenGL.GLUT.special.cleanupWindowContext` answers with a flag and raises
nothing.
"""
import logging

import pytest

from OpenGL import contextdata
from OpenGL.GLUT import special


@pytest.fixture
def store(monkeypatch):
    """The context store and GLUT standing in, so no window is needed"""
    seen = {}
    monkeypatch.setattr(special.GLUT, 'glutSetWindow',
                        lambda window: seen.__setitem__('current', window),
                        raising=False)
    monkeypatch.setattr(contextdata, 'getContext', lambda: 'ctx')
    monkeypatch.setattr(contextdata, 'cleanupContext',
                        lambda context: seen.__setitem__('cleaned', context))
    return seen


def _fails(monkeypatch, message='no valid context'):
    def raiser():
        raise RuntimeError(message)
    monkeypatch.setattr(contextdata, 'getContext', raiser)


def test_the_window_s_context_data_is_dropped(store):
    assert special.cleanupWindowContext(7) is True
    assert store['current'] == 7
    assert store['cleaned'] == 'ctx'


def test_a_context_that_cannot_be_found_is_reported_not_raised(store, monkeypatch):
    """The caller is about to destroy the window and must not be stopped."""
    _fails(monkeypatch)
    assert special.cleanupWindowContext(7) is False


def test_the_report_says_what_went_wrong(store, monkeypatch, caplog):
    _fails(monkeypatch, 'no valid context')
    with caplog.at_level(logging.ERROR, logger=special._log.name):
        special.cleanupWindowContext(7)
    assert 'no valid context' in caplog.text
