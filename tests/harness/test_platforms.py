"""Which binding a Tk widget's context is made through, by platform."""

import pytest

import platforms


@pytest.mark.parametrize('platform,library', [
    ('darwin', 'CGL'),
    ('win32', 'WGL'),
    ('linux', 'GLX'),
    ('freebsd14', 'GLX'),
    ('openbsd7', 'GLX'),
    ('netbsd9', 'GLX'),
    ('dragonfly6', 'GLX'),
])
def test_each_platform_opengl_tk_serves_has_its_binding(platform, library):
    assert platforms.window_system_library(platform) == library


@pytest.mark.parametrize('platform', [
    'android', 'ios', 'emscripten', 'wasi', 'cygwin', 'haiku1',
])
def test_a_platform_it_does_not_serve_has_none(platform):
    """Rather than a default that has the cases try, and fail, to make a
    context there."""
    assert platforms.window_system_library(platform) is None


def test_asking_for_no_binding_skips():
    mark = platforms.needs(None)
    assert mark.name == 'skip' and 'no window-system binding' in mark.kwargs['reason']


def test_this_machine_is_answered_when_no_platform_is_named():
    import sys

    assert platforms.window_system_library() \
        == platforms.window_system_library(sys.platform)
