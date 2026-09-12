#! /usr/bin/env python3
"""A platform plugin that will not import says which, and why.

``OpenGL.platform._load`` picks a plugin for the machine and imports it. Where
that import fails -- a missing library, a broken install, an OpenGL that is
not where the loader looks -- ``PlatformPlugin.load`` writes a warning to a
logger nobody has configured and answers ``None``. ``_load`` then called it:

    plugin = plugin_class()
    TypeError: 'NoneType' object is not callable

which is what #43 is. The caller is told nothing: not which plugin, not that a
plugin was involved, and not the ImportError that actually happened, since
that went only to the log. Every reply on that ticket is the maintainer asking
the reporter to run something by hand to recover the message PyOpenGL already
had and discarded.

It is the first thing a broken install does, so it is the error most likely to
be somebody's first contact with PyOpenGL.

https://github.com/mcfletch/pyopengl/issues/43
"""

import pytest

from OpenGL import plugins
import OpenGL.platform


@pytest.fixture
def failing_plugin(monkeypatch):
    """Every plugin refuses to import, as a missing library makes them."""
    monkeypatch.setattr(plugins.PlatformPlugin, 'load',
                        lambda self: None, raising=True)


class TestWhenThePluginWillNotImport:
    def test_it_is_an_import_error_rather_than_a_type_error(self, failing_plugin):
        """A TypeError says a bug; an ImportError says a missing thing."""
        with pytest.raises(ImportError):
            OpenGL.platform._load()

    def test_it_names_the_plugin_that_failed(self, failing_plugin):
        with pytest.raises(ImportError) as raised:
            OpenGL.platform._load()
        message = str(raised.value)
        assert 'OpenGL.platform' in message, message

    def test_it_says_where_the_reason_is(self, failing_plugin):
        """The ImportError itself went to the log, so the caller has to be
        told the log is where it is -- otherwise the message names a failure
        with no way to find out what it was."""
        with pytest.raises(ImportError) as raised:
            OpenGL.platform._load()
        message = str(raised.value).lower()
        assert 'log' in message, message

    def test_the_platform_module_is_left_alone(self, failing_plugin):
        """A failed load must not install half a platform over the working
        one: whatever a caller had a moment ago still answers."""
        before = OpenGL.platform.PLATFORM
        with pytest.raises(ImportError):
            OpenGL.platform._load()
        assert OpenGL.platform.PLATFORM is before


def test_a_working_platform_still_loads():
    """The ordinary path, which the guard above must not have broken."""
    assert OpenGL.platform._load() is not None
    assert OpenGL.platform.PLATFORM is not None
