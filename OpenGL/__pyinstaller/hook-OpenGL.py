"""What a frozen application needs from PyOpenGL beyond its import statements

Three things are invisible to a tool that follows imports:

* the declaration tables under ``OpenGL/raw/_declarations``, which every module
  in :mod:`OpenGL.raw` is built from -- those modules are not shipped as files,
  so nothing in the import graph points at the data that answers for them;
* the plug-in registries (:mod:`OpenGL.plugins`), which name every platform
  module and array format handler as a string and import it only once
  something matches, and
* the GLUT and GLE DLLs shipped for Windows, which
  :mod:`OpenGL.platform.ctypesloader` opens by path.

The last two are reported from the same source the running library uses, so a
plug-in added to PyOpenGL is carried into a frozen application without an edit
here.
"""

import os

from PyInstaller import isolated
from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import collect_data_files


@isolated.decorate
def _plugin_modules():
    """Modules the PyOpenGL plug-in registries would import"""
    from OpenGL import plugins

    return plugins.registered_modules('OpenGL')


@isolated.decorate
def _dll_directory():
    """Where the running library looks for its bundled Windows DLLs"""
    from OpenGL.platform import ctypesloader

    return ctypesloader.DLL_DIRECTORY


# Every platform's module, not only the one being built for: which is used is
# settled at run time from ``PYOPENGL_PLATFORM`` and the session type, so a
# frozen application that is told to use EGL or OSMesa needs the module to be
# there. They are small and pure Python.
hiddenimports = _plugin_modules()

# Without these there is no OpenGL.raw at all: the finder that answers for
# those names reads the tables to learn which names it can answer for, so an
# application frozen without them fails on the first `from OpenGL.raw...
# import`, several frames away from the missing data.
datas = collect_data_files('OpenGL', includes=['raw/_declarations/*.dat'])

if is_win:
    # `ctypesloader` opens these by path out of a directory beside the package,
    # so they are collected from that directory rather than from anywhere the
    # installer happened to put a copy -- if the running library would not find
    # a file, a frozen application has no use for it either.
    _directory = _dll_directory()
    _names = sorted(os.listdir(_directory)) if os.path.isdir(_directory) else []
    binaries = [
        (os.path.join(_directory, name), os.path.join('OpenGL', 'DLLS'))
        for name in _names
        if name.lower().endswith('.dll')
    ]
