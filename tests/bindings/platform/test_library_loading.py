#! /usr/bin/env python3
"""Which file the loader is asked to open, for a given library name.

Linux has its own path through :func:`OpenGL.platform.ctypesloader.loadLibrary`;
everything else -- Windows and macOS both -- goes through
``_loadLibraryWindows``, and the two want opposite things from
``ctypes.util.find_library``.

On Windows it walks ``PATH``, which is the wrong place to look for a library
that belongs to the operating system (#174).  On macOS it answers a framework
path, and since Big Sur the frameworks are in the dynamic linker cache rather
than on the filesystem, so nothing may check that the path names a file before
handing it to ``dlopen`` (#55).

Neither question is about the load itself, only about the choice, so the loader
is stood in for and these run on any machine.

https://github.com/mcfletch/pyopengl/issues/174
https://github.com/mcfletch/pyopengl/issues/55
"""

import os
import sys
import types

import pytest

import OpenGL
from OpenGL.platform import ctypesloader


class RecordingLoader:
    """Stands in for ``ctypes.windll`` or ``ctypes.cdll``.

    Records every name it was handed, and loads the ones it was told to. A
    name it was not told to load raises, which is what a wrong architecture,
    a missing dependency or an absent file all look like from here.
    """

    def __init__(self, loadable=None):
        #: Every name handed to the loader, in the order it was tried.
        self.tried = []
        #: The names that load. ``None`` means all of them do.
        self.loadable = loadable

    def __call__(self, name, mode=None):
        self.tried.append(name)
        if self.loadable is not None and name not in self.loadable:
            raise OSError(-1, 'no such library', name)
        return 'the library at %s' % (name,)


@pytest.fixture
def on_path(monkeypatch):
    """``find_library`` answers with a copy on ``PATH``, as conda's does.

    Installing PyOpenGL from conda-forge puts ``Library\\bin`` -- which carries
    a Mesa ``opengl32.dll`` -- ahead of ``System32`` on ``PATH``, so this is
    what ``find_library`` returns on that machine for every name it is asked.
    """

    def find_library(name):
        return 'C:\\conda\\Library\\bin\\%s.dll' % (name,)

    monkeypatch.setattr(ctypesloader.util, 'find_library', find_library)


@pytest.fixture
def found_by_nothing(monkeypatch):
    """``find_library`` knows no library at all."""
    monkeypatch.setattr(ctypesloader.util, 'find_library', lambda name: None)


class TestALibraryWindowsItselfProvides:
    """``System32`` before ``PATH``, which is what Windows' own search does.

    ``C:\\Windows\\System32\\opengl32.dll`` is a trampoline to whatever the
    graphics driver installed, so it is always the right one. Asking
    ``find_library`` first meant the answer came from ``PATH`` instead, and a
    program that wanted the driver's GL got Mesa with nothing saying so.
    """

    @pytest.mark.parametrize('name', sorted(ctypesloader.SYSTEM_LIBRARIES))
    def test_the_bare_name_reaches_the_loader(self, name, on_path):
        """Bare, so that Windows resolves it: the system directory comes
        before ``PATH`` in the loader's search order, and ``PATH`` is the only
        place ``find_library`` looks."""
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, name, 0)
        assert loader.tried == [name]

    @pytest.mark.parametrize('name', sorted(ctypesloader.SYSTEM_LIBRARIES))
    def test_find_library_is_not_consulted_at_all(self, name, monkeypatch):
        def refuse(name):
            raise AssertionError('find_library was asked about %r' % (name,))

        monkeypatch.setattr(ctypesloader.util, 'find_library', refuse)
        ctypesloader._loadLibraryWindows(RecordingLoader(), name, 0)

    def test_the_name_matches_whatever_case_the_caller_used(self, on_path):
        """The platform module spells it ``opengl32``; a caller need not."""
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, 'OpenGL32', 0)
        assert loader.tried == ['OpenGL32']

    def test_a_library_windows_does_not_provide_still_goes_through_path(
        self, on_path
    ):
        """freeglut is not part of Windows, and where the user put it is
        exactly what ``PATH`` is for."""
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, 'freeglut64.vc14', 0)
        assert loader.tried == ['C:\\conda\\Library\\bin\\freeglut64.vc14.dll']


class TestALibraryFindLibraryDoesNotKnow:
    """The bundled copy, then the bare name."""

    @pytest.fixture
    def bundled(self, monkeypatch, tmp_path):
        """``OpenGL/DLLS`` holding one library, as a Windows install does."""
        monkeypatch.setattr(ctypesloader, 'DLL_DIRECTORY', str(tmp_path))
        (tmp_path / 'freeglut64.vc14.dll').write_bytes(b'')
        return str(tmp_path / 'freeglut64.vc14.dll')

    def test_the_bundled_copy_is_tried_first(self, found_by_nothing, bundled):
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, 'freeglut64.vc14', 0)
        assert loader.tried == [bundled]

    def test_the_bare_name_is_tried_when_the_bundled_copy_will_not_load(
        self, found_by_nothing, bundled
    ):
        """A 32-bit build of the library in a 64-bit process is a file that
        exists and does not load, and the loader has somewhere else to look."""
        loader = RecordingLoader(loadable=['freeglut64.vc14'])
        assert ctypesloader._loadLibraryWindows(loader, 'freeglut64.vc14', 0)
        assert loader.tried == [bundled, 'freeglut64.vc14']

    def test_the_bare_name_is_tried_when_there_is_no_bundled_copy(
        self, found_by_nothing, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(ctypesloader, 'DLL_DIRECTORY', str(tmp_path))
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, 'freeglut', 0)
        assert loader.tried == ['freeglut']

    def test_the_failure_names_the_library_that_was_asked_for(
        self, found_by_nothing, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(ctypesloader, 'DLL_DIRECTORY', str(tmp_path))
        loader = RecordingLoader(loadable=[])
        with pytest.raises(OSError) as raised:
            ctypesloader._loadLibraryWindows(loader, 'freeglut', 0)
        assert 'freeglut' in raised.value.args


class TestAMacOSFramework:
    """Big Sur stopped keeping the system libraries as files.

    ``find_library`` was taught about the dynamic linker cache in CPython
    3.8.10 and 3.9.1, so on a supported interpreter it answers. Where it does
    not, the framework path is the fallback -- and it is handed straight to
    ``dlopen``, because asking whether the file exists is the thing Big Sur's
    release note says will now always answer no.
    """

    @pytest.fixture
    def frameworks(self, monkeypatch, tmp_path):
        """A macOS ``FRAMEWORK_DIRECTORIES``, with nothing on disk under it."""
        monkeypatch.setattr(ctypesloader, 'DLL_DIRECTORY', str(tmp_path))
        monkeypatch.setattr(
            ctypesloader, 'FRAMEWORK_DIRECTORIES', ['/System/Library/Frameworks']
        )

    def test_the_framework_path_is_tried(self, found_by_nothing, frameworks):
        loader = RecordingLoader(
            loadable=['/System/Library/Frameworks/OpenGL.framework/OpenGL']
        )
        assert ctypesloader._loadLibraryWindows(loader, 'OpenGL', 0)
        assert loader.tried[-1] == (
            '/System/Library/Frameworks/OpenGL.framework/OpenGL'
        )

    def test_nothing_asks_whether_the_framework_is_a_file(
        self, found_by_nothing, frameworks, monkeypatch
    ):
        """Which is the whole of #55: on Big Sur it is not one, and it loads.

        The bundled-DLL directory is still asked about, because that one holds
        ordinary files on the platform it is for.
        """
        was = os.path.isfile

        def refuse(path):
            if '.framework' in path:
                raise AssertionError('asked whether %r is a file' % (path,))
            return was(path)

        monkeypatch.setattr(os.path, 'isfile', refuse)
        loader = RecordingLoader(
            loadable=['/System/Library/Frameworks/GLUT.framework/GLUT']
        )
        assert ctypesloader._loadLibraryWindows(loader, 'GLUT', 0)

    def test_find_library_still_wins_where_it_answers(self, on_path, frameworks):
        """A framework somewhere else -- a bundled one, a homebrew one -- is
        what ``find_library`` is for; the path below is only the fallback."""
        loader = RecordingLoader()
        ctypesloader._loadLibraryWindows(loader, 'OpenGL', 0)
        assert loader.tried == ['C:\\conda\\Library\\bin\\OpenGL.dll']


class TestWhereTheBundledLibrariesAre:
    """The prebuilt freeglut and GLE builds are a distribution of their own.

    ``PyOpenGL-glut-binaries``, which a Windows user asks for as ``pip install
    PyOpenGL[glut]``. So the directory is wherever that package was installed,
    and this one falls back to the copy it used to carry -- an install made
    before the split, and this checkout, both still have one.

    Only the *directory* moves. What is looked for in it, and the order a
    system library is preferred in, are unchanged: see the cases above.

    See ``plans/BUNDLED-DLLS.md``.
    """

    @pytest.fixture
    def installed(self, monkeypatch, tmp_path):
        """``pyopengl_glut_binaries`` is installed and says where its files are."""
        module = types.ModuleType('pyopengl_glut_binaries')
        module.DLL_DIRECTORY = str(tmp_path)
        monkeypatch.setitem(sys.modules, 'pyopengl_glut_binaries', module)
        return str(tmp_path)

    @pytest.fixture
    def not_installed(self, monkeypatch):
        """It is absent, which is what a plain ``pip install PyOpenGL`` gives.

        ``None`` in ``sys.modules`` is how the import system spells "this name
        does not resolve", and it answers without touching the filesystem.
        """
        monkeypatch.setitem(sys.modules, 'pyopengl_glut_binaries', None)

    def test_the_package_is_where_they_come_from(self, installed):
        assert ctypesloader._bundled_dll_directory() == installed

    def test_without_it_the_copy_inside_this_package_is_used(self, not_installed):
        assert ctypesloader._bundled_dll_directory() == os.path.join(
            os.path.dirname(OpenGL.__file__), 'DLLS'
        )

    def test_a_package_too_old_to_say_is_the_same_as_none(self, monkeypatch):
        """A ``pyopengl_glut_binaries`` without the attribute is one this
        PyOpenGL does not know how to ask, not a reason to raise out of the
        import that happened to be first."""
        monkeypatch.setitem(
            sys.modules, 'pyopengl_glut_binaries',
            types.ModuleType('pyopengl_glut_binaries'),
        )
        assert ctypesloader._bundled_dll_directory() == os.path.join(
            os.path.dirname(OpenGL.__file__), 'DLLS'
        )

    def test_the_constant_the_loader_reads_is_what_the_lookup_answered(self):
        """``DLL_DIRECTORY`` is the name ``_loadLibraryWindows`` joins onto and
        the name the cases above monkeypatch, so the lookup has to be what
        computes it rather than a second copy of the same rule."""
        assert ctypesloader.DLL_DIRECTORY == ctypesloader._bundled_dll_directory()


class TestWhereAFrozenApplicationHasToPutThem:
    """A freezer collects from ``DLL_DIRECTORY`` and writes into a bundle.

    The running loader in that bundle performs the same lookup, so the two
    have to agree: an application that put the libraries under ``OpenGL`` and
    then looked for them under ``pyopengl_glut_binaries`` carries them and
    cannot load them, and says so as ``glutInit`` being undefined.
    """

    def destination(self, monkeypatch, directory):
        monkeypatch.setattr(ctypesloader, 'DLL_DIRECTORY', directory)
        return ctypesloader._bundled_dll_destination()

    def test_the_binaries_package_keeps_its_own_name(self, monkeypatch):
        assert self.destination(
            monkeypatch,
            os.path.join('any', 'where', 'pyopengl_glut_binaries', 'DLLS'),
        ) == os.path.join('pyopengl_glut_binaries', 'DLLS')

    def test_the_fallback_keeps_openglslash_dlls(self, monkeypatch):
        assert self.destination(
            monkeypatch, os.path.join('any', 'where', 'OpenGL', 'DLLS')
        ) == os.path.join('OpenGL', 'DLLS')

    def test_it_follows_the_lookup_rather_than_naming_a_package(self, monkeypatch):
        """Nothing here spells either package name, so a rename of the
        providing distribution does not silently break freezing."""
        assert self.destination(
            monkeypatch, os.path.join('any', 'where', 'renamed_later', 'DLLS')
        ) == os.path.join('renamed_later', 'DLLS')

    def test_it_describes_the_directory_the_loader_actually_uses(self):
        """Against the real value rather than a constructed one."""
        destination = ctypesloader._bundled_dll_destination()
        assert ctypesloader.DLL_DIRECTORY.endswith(destination), (
            destination, ctypesloader.DLL_DIRECTORY)


class TestWhatEachPlatformLooksIn:
    def test_only_macos_has_framework_directories(self):
        """A Linux or Windows load must not go looking under ``/System``."""
        if sys.platform == 'darwin':
            assert ctypesloader.FRAMEWORK_DIRECTORIES
        else:
            assert ctypesloader.FRAMEWORK_DIRECTORIES == []
