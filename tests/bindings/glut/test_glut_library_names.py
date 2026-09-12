#! /usr/bin/env python3
"""Which GLUT libraries the Windows platform looks for.

Three tickets are the same report: ``glutInit`` or ``glutInitDisplayMode`` is
an undefined function on Windows. #76 says why. The reporter downloaded the
official freeglut, put it on ``PATH``, and got the same error -- because the
only names asked for were the bundled builds' own, ``freeglut64.vc14.dll`` and
``glut64.vc14.dll``, and nothing ships under those names but us. They found it
by reading the source, renamed the file, and it worked.

So the names a GLUT the *user* installed actually has are asked for too, and
first, because a user who installed one meant it. What is under test is the
choice of names, so the loader is stood in for and these run on any machine.

https://github.com/mcfletch/pyopengl/issues/76
https://github.com/mcfletch/pyopengl/issues/125
https://github.com/mcfletch/pyopengl/issues/127
"""

import ctypes
import sys

import pytest


class FakeWinDLL:
    """``ctypes.windll``, for a machine that is not Windows.

    Reached only by the module's own ``GDI32``, which these cases do not go
    near.
    """

    def __getattr__(self, name):
        return 'windll.%s' % (name,)


@pytest.fixture
def win32(monkeypatch):
    """``OpenGL.platform.win32``, imported wherever this runs.

    Two of the names it reads at import are Windows' own --
    ``ctypes.WINFUNCTYPE`` and ``ctypes.windll`` -- and neither has anything to
    do with which libraries the platform looks for, so both are stood in for.

    The module is dropped afterwards, so that nothing later in the run finds a
    Windows platform module built on the stand-ins.
    """
    import OpenGL.platform

    monkeypatch.setattr(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE, raising=False)
    monkeypatch.setattr(ctypes, 'windll', FakeWinDLL(), raising=False)
    already = sys.modules.get('OpenGL.platform.win32')
    try:
        import OpenGL.platform.win32 as module

        yield module
    finally:
        if already is None:
            sys.modules.pop('OpenGL.platform.win32', None)
            if getattr(OpenGL.platform, 'win32', None) is not None:
                del OpenGL.platform.win32


class RecordingLoader:
    """Stands in for ``ctypesloader.loadLibrary``.

    Records the names it was asked for and loads only the ones named, which is
    how a machine that has one GLUT and not another answers.
    """

    def __init__(self, loadable=()):
        self.tried = []
        self.loadable = list(loadable)

    def __call__(self, dllType, name, mode=None):
        self.tried.append(name)
        if name not in self.loadable:
            raise OSError(-1, 'no such library', name)
        return 'the library at %s' % (name,)


@pytest.fixture
def loader(win32, monkeypatch):
    recorder = RecordingLoader()
    monkeypatch.setattr(win32.ctypesloader, 'loadLibrary', recorder)
    return recorder


@pytest.fixture
def platform(win32):
    """A Win32Platform with nothing loaded.

    ``GLUT`` is a lazy property, so reading it once is the whole of the
    behaviour under test.
    """
    return win32.Win32Platform()


@pytest.fixture
def bundled(win32):
    """The name of the freeglut build this package bundles for this
    interpreter -- ``freeglut64.vc14`` on a current 64-bit Python."""
    return 'freeglut%s.%s' % (win32.size, win32.vc)


class TestAGlutTheUserInstalled:
    """The names a GLUT that did not come from us actually has."""

    @pytest.mark.parametrize(
        'name',
        [
            # What the official freeglut Windows binaries, MSYS2 and vcpkg
            # all install.
            'freeglut',
            # The original GLUT.  The 32 is the Win32 API rather than the word
            # size, so this is the name on a 64-bit machine too.
            'glut32',
        ],
    )
    def test_it_is_found(self, platform, loader, name):
        loader.loadable = [name]
        assert platform.GLUT == 'the library at %s' % (name,)

    def test_freeglut_is_preferred_to_the_bundled_build(
        self, platform, loader, bundled
    ):
        """A user who installed one meant it, and theirs is the one that gets
        security fixes."""
        loader.loadable = ['freeglut', bundled]
        assert platform.GLUT == 'the library at freeglut'

    def test_freeglut_is_preferred_to_the_original_glut(self, platform, loader):
        """Which is what the loop has always done, and the reason it is a loop
        rather than one name."""
        loader.loadable = ['freeglut', 'glut32']
        assert platform.GLUT == 'the library at freeglut'


class TestTheBundledBuild:
    def test_it_is_still_found_when_the_machine_has_no_other(
        self, platform, loader, bundled
    ):
        loader.loadable = [bundled]
        assert platform.GLUT == 'the library at %s' % (bundled,)

    def test_the_bundled_glut_is_the_last_resort(self, platform, loader, win32):
        loader.loadable = ['glut%s.%s' % (win32.size, win32.vc)]
        assert platform.GLUT


class TestAMachineWithNoGlutAtAll:
    def test_the_answer_is_none_rather_than_an_error(self, platform, loader):
        """Which is what ``OpenGL.GLUT`` reads as "no entry points here": the
        namespace imports, and calling one raises NullFunctionError."""
        assert platform.GLUT is None

    def test_every_name_was_tried(self, platform, loader, bundled):
        assert platform.GLUT is None
        assert 'freeglut' in loader.tried
        assert bundled in loader.tried

    def test_a_library_of_the_wrong_architecture_does_not_stop_the_search(
        self, platform, loader, bundled
    ):
        """A 32-bit freeglut on a 64-bit ``PATH`` is a file that exists and
        will not load, and it must not shadow the build that would."""
        loader.loadable = [bundled]
        assert platform.GLUT == 'the library at %s' % (bundled,)
        assert loader.tried.index('freeglut') < loader.tried.index(bundled)
