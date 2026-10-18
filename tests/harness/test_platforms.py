"""Which binding a Tk widget's context is made through, by platform."""

import pytest

import platforms


@pytest.mark.parametrize('platform,library', [
    ('darwin', 'CGL'),
    ('win32', 'WGL'),
    ('linux', 'GLX'),
    ('freebsd14', 'GLX'),
])
def test_each_platform_has_its_binding(platform, library):
    assert platforms.window_system_library(platform) == library
