"""What a frozen application needs from PyOpenGL beyond its import statements

Three things are invisible to a tool that follows imports:

* the declaration tables under ``OpenGL/raw/_declarations``, which every module
  in :mod:`OpenGL.raw` is built from -- those modules are not shipped as files,
  so nothing in the import graph points at the data that answers for them;
* the plug-in registries (:mod:`OpenGL.plugins`), which name every platform
  module and array format handler as a string and import it only once
  something matches -- and the same for each API's error checker, which every
  binding is built against, and for the Tk widget's context implementations
  (:data:`OpenGL.Tk.context.IMPLEMENTATIONS`), and
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
def _error_modules():
    """The per-API error checkers, which every binding imports by name

    :mod:`OpenGL._declarations` builds each binding against
    ``OpenGL.raw.<api>._errors``, named as a string and imported when the
    binding is first built.  Only GL's and EGL's are imported anywhere
    statically, so an application frozen without the rest opens its window and
    fails on the first call into GLU, GLX, WGL or an ES binding.

    Found by looking for them, so an API added to the library is carried
    without an edit here.
    """
    import os

    import OpenGL.raw

    root = os.path.dirname(OpenGL.raw.__file__)
    return sorted(
        'OpenGL.raw.%s._errors' % (name,)
        for name in os.listdir(root)
        if os.path.exists(os.path.join(root, name, '_errors.py'))
    )


@isolated.decorate
def _tk_context_modules():
    """Modules the Tk GL widget would import to make a context

    It makes one through the window system's own API -- GLX or WGL -- and which
    of them is settled at run time from the windowing system Tk turns out to be
    running on, so both are named as strings and neither is in the import graph.
    An application frozen without them builds cleanly, opens its window, and
    fails on the context.

    Nothing where tkinter is not installed: an application that does not use the
    Tk backend has no use for these, and a build host without tkinter is exactly
    such an application.
    """
    try:
        from OpenGL.Tk.context import IMPLEMENTATIONS
    except ImportError:
        return []
    return sorted({module for module, _class in IMPLEMENTATIONS.values()})


@isolated.decorate
def _dll_layout():
    """Where the prebuilt Windows libraries are, and where they must go

    Two answers rather than one because the destination is not a constant: the
    builds ship as ``PyOpenGL-glut-binaries`` where the user asked for
    ``PyOpenGL[glut]`` and are absent otherwise, and the loader computes the
    directory from whichever package provided them.  A bundle that reproduced
    the other layout would carry the libraries and not find them.
    """
    from OpenGL.platform import ctypesloader

    return ctypesloader.DLL_DIRECTORY, ctypesloader._bundled_dll_destination()


# Every platform's module, not only the one being built for: which is used is
# settled at run time from ``PYOPENGL_PLATFORM`` and the session type, so a
# frozen application that is told to use EGL or OSMesa needs the module to be
# there. They are small and pure Python. The Tk widget's context
# implementations are chosen the same way and are the same size.
hiddenimports = _plugin_modules() + _error_modules() + _tk_context_modules()

# Without these there is no OpenGL.raw at all: the finder that answers for
# those names reads the tables to learn which names it can answer for, so an
# application frozen without them fails on the first `from OpenGL.raw...
# import`, several frames away from the missing data.
datas = collect_data_files('OpenGL', includes=['raw/_declarations/*.dat'])

if is_win:
    # `ctypesloader` opens these by path out of the package that provides
    # them, so they are collected from that directory rather than from
    # anywhere the installer happened to put a copy -- if the running library
    # would not find a file, a frozen application has no use for it either.
    #
    # A machine with no `PyOpenGL-glut-binaries` and no leftover `OpenGL/DLLS`
    # has nothing to collect, and the application is frozen without GLUT. That
    # is the right answer rather than an error: `OpenGL.GLUT` is optional, and
    # a build host that did not install the extra did not ask for it.
    _directory, _into = _dll_layout()
    _names = sorted(os.listdir(_directory)) if os.path.isdir(_directory) else []
    binaries = [
        (os.path.join(_directory, name), _into)
        for name in _names
        if name.lower().endswith('.dll')
    ]
    # Without this the module is not in the bundle, the loader's import of it
    # fails there, and it falls back to `OpenGL/DLLS` -- which is not where
    # the files above were put.
    if _names and not _into.startswith('OpenGL'):
        hiddenimports = hiddenimports + ['pyopengl_glut_binaries']
