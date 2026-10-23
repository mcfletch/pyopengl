"""``OpenGL.EGL.debug`` reporting a config whose attributes a driver refuses."""

import logging

import pytest

try:
    from OpenGL.EGL import debug
except ImportError as err:  # an EGL library is needed to import OpenGL.EGL
    pytest.skip('OpenGL.EGL will not import here: %s' % (err,), allow_module_level=True)


class TestDebugConfig:
    def test_a_refused_attribute_is_logged_and_skipped(self, monkeypatch, caplog):
        monkeypatch.setattr(debug, 'eglGetConfigAttrib', lambda *args: False)
        with caplog.at_level(logging.WARNING):
            assert debug.debug_config(None, None) == {}
        assert 'Failed to get attribute' in caplog.text
