"""A stand-in import finder for ``OpenGL.raw.*`` that defers configuration.

The generated ``OpenGL.raw`` modules are not shipped, so a finder must be on
``sys.meta_path`` before the first such import.  PyOpenGL makes that import
itself, three lines into ``import OpenGL.GL``, so the finder is installed
during ``import OpenGL``.  At that point the configuration flags are not yet
set.  A program sets ``OpenGL.ERROR_CHECKING`` and the other flags in the
lines *after* ``import OpenGL``, and ``OpenGL._configflags`` reads them all
the first time it is imported.

This module therefore imports nothing from PyOpenGL.  It stands in for the
real finder until the first ``OpenGL.raw.*`` import.  By then the program has
set its flags, and the real finder is built and handles the import.
"""

import os
import sys

__all__ = ['install', 'uninstall']

#: Every name the real finder handles starts with this prefix.  Other names
#: are declined without loading anything.
PREFIX = 'OpenGL.raw.'

_installed = None


class _DeferredRawFinder:
    """Loads the real finder on the first *generated* ``OpenGL.raw.*`` import.

    The stand-in keeps its own index of generated module names.  Reading the
    index costs a marshal load and imports nothing that reads a configuration
    flag.  A name the tables do not list, such as ``OpenGL.raw.GL._types``
    (a real file), is declined without loading the real finder.
    """

    def __init__(self):
        self._names = None
        self._real = False

    def _generated(self, name):
        if self._names is None:
            from OpenGL import _declarations

            self._names = frozenset(
                _declarations.data_declarations().module_names()
            )
        return name in self._names

    def _delegate(self):
        if self._real is False:
            from OpenGL._dispatch import finder

            # install() puts the real finder on sys.meta_path, and this
            # stand-in is removed, so later imports go to the real finder.
            self._real = finder.install()
            if self._real is not None:
                _remove(self)
        return self._real

    def find_spec(self, name, path=None, target=None):
        if not name.startswith(PREFIX) or not self._generated(name):
            return None
        real = self._delegate()
        if real is None:
            return None
        return real.find_spec(name, path, target)


def _remove(entry):
    try:
        sys.meta_path.remove(entry)
    except ValueError:
        pass


def install():
    """Put the stand-in ahead of the path finder."""
    global _installed
    if _installed is None:
        _installed = _DeferredRawFinder()
        sys.meta_path.insert(0, _installed)
    return _installed


def uninstall():
    global _installed
    if _installed is not None:
        _remove(_installed)
        _installed = None
