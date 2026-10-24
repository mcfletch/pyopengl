"""PyInstaller hook for the PyOpenGL files that import tracing cannot find.

A tool that follows import statements misses three kinds of file:

* the declaration tables under ``OpenGL/raw/_declarations``.  Every module in
  :mod:`OpenGL.raw` is built from them at import time and is not shipped as a
  file, so the import graph does not reach the tables.
* modules imported by name from a string.  The plug-in registries
  (:mod:`OpenGL.plugins`) name every platform module and array format handler
  this way, and import one only when it matches.  Each API's error checker
  and the Tk widget's context implementations
  (:data:`OpenGL.Tk.context.IMPLEMENTATIONS`) are imported the same way.
* the GLUT and GLE DLLs shipped for Windows, which
  :mod:`OpenGL.platform.ctypesloader` opens by path.

The modules and DLLs are listed from the same sources the running library
uses, so a plug-in added to PyOpenGL is bundled without a change to this hook.
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
    """The per-API error checker modules, which every binding imports by name

    :mod:`OpenGL._declarations` builds each binding against
    ``OpenGL.raw.<api>._errors``, imported by name when the binding is first
    built.  Only the GL and EGL checkers have static imports.  An application
    frozen without the others opens its window, then fails on the first call
    into GLU, GLX, WGL or an ES binding.

    The modules are found by searching the package, so a new API is bundled
    without a change here.
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

    The widget creates its context with the window system's API (GLX or WGL).
    The choice depends on the windowing system Tk runs on, and is made at run
    time.  Both modules are named as strings, so neither is in the import
    graph.  An application frozen without them builds and opens its window,
    then fails to create the context.

    Returns an empty list when tkinter is not installed.  A build host without
    tkinter cannot be building an application that uses the Tk backend.
    """
    try:
        from OpenGL.Tk.context import IMPLEMENTATIONS
    except ImportError:
        return []
    return sorted({module for module, _class in IMPLEMENTATIONS.values()})


@isolated.decorate
def _dll_layout():
    """The directory of the prebuilt Windows libraries, and their destination

    The destination depends on the installation.  The libraries come from
    ``PyOpenGL-glut-binaries`` when the user installed ``PyOpenGL[glut]``, and
    are absent otherwise.  The loader computes their directory from the
    package that provides them.  A bundle using a different layout would
    include the libraries, and the loader would not find them.
    """
    from OpenGL.platform import ctypesloader

    return ctypesloader.DLL_DIRECTORY, ctypesloader._bundled_dll_destination()


# Every platform's module is bundled, including other platforms'.  The
# platform is chosen at run time from ``PYOPENGL_PLATFORM`` and the session
# type, so a frozen application set to use EGL or OSMesa needs that module.
# The modules are small and pure Python.  The Tk widget's context
# implementations are chosen the same way, and are as small.
hiddenimports = _plugin_modules() + _error_modules() + _tk_context_modules()

# OpenGL.raw cannot be imported without these tables.  Its import finder
# reads them to learn which module names exist.  An application frozen
# without them fails on the first `from OpenGL.raw... import`, with a
# traceback several frames away from the missing data.
datas = collect_data_files('OpenGL', includes=['raw/_declarations/*.dat'])

if is_win:
    # `ctypesloader` opens these by path from the package that provides them,
    # so they are collected from that directory.  Copies elsewhere are
    # ignored, because the running library would not load them either.
    #
    # A machine with no `PyOpenGL-glut-binaries` and no leftover `OpenGL/DLLS`
    # has nothing to collect, and the application is frozen without GLUT.
    # This is not an error, because `OpenGL.GLUT` is optional and the build
    # host did not install the extra.
    _directory, _into = _dll_layout()
    _names = sorted(os.listdir(_directory)) if os.path.isdir(_directory) else []
    binaries = [
        (os.path.join(_directory, name), _into)
        for name in _names
        if name.lower().endswith('.dll')
    ]
    # Without this the module is not bundled.  The loader's import of it
    # fails, and the loader falls back to `OpenGL/DLLS`, where the files
    # above were not put.
    if _names and not _into.startswith('OpenGL'):
        hiddenimports = hiddenimports + ['pyopengl_glut_binaries']
