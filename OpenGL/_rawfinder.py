"""Answer for ``OpenGL.raw.*`` without deciding anything yet.

The generated modules are not shipped, so a finder has to be on
``sys.meta_path`` before anything imports one -- and the first thing that does
is PyOpenGL itself, three lines into ``import OpenGL.GL``.  That means
installing at ``import OpenGL``, which is the one moment nothing may be
decided: a program sets ``OpenGL.ERROR_CHECKING`` and its neighbours in the
lines *after* that import, and ``OpenGL._configflags`` reads all of them the
first time it is imported.

So this module imports nothing from PyOpenGL, and stands in for the real finder
until an ``OpenGL.raw.*`` name is actually asked for.  By then the program has
finished configuring, and the real finder can be built and asked to answer.
"""

import os
import sys

__all__ = ['install', 'uninstall', 'virtual_modules_wanted']

#: Every name the real finder can answer for is under here, so a name that is
#: not is one to decline without loading anything to find that out.
PREFIX = 'OpenGL.raw.'

_YES = ('1', 'true', 'yes', 'on')


def virtual_modules_wanted():
    """Whether ``OpenGL.raw.*`` is built from the tables rather than imported.

    On, because there are no files to import: the generated modules under
    ``OpenGL/raw`` hold nothing the declaration tables do not, and a module that
    is data does not need to be a module.  ``PYOPENGL_VIRTUAL_MODULES=0`` goes
    back to the files, which is useful only to a tree that still has them.

    The parse lives here, in the one module that imports nothing from PyOpenGL,
    because both readers of the flag need it and two parses of one variable can
    disagree after an edit.  ``OpenGL._configflags`` cannot be one of them: it
    reads every flag off ``OpenGL`` the first time it is imported, and the
    finder is reached before a program has finished setting them.

    An empty value means unset, because that is what an unexported shell
    variable expands to.
    """
    value = os.environ.get('PYOPENGL_VIRTUAL_MODULES', '').strip().lower()
    return (value or '1') in _YES

_installed = None


class _DeferredRawFinder:
    """Loads the real finder on the first *generated* ``OpenGL.raw.*`` import.

    It keeps the index of names itself.  Reading it costs a marshal load and
    imports nothing that reads a configuration flag, and it is what lets a name
    the tables do not describe -- ``OpenGL.raw.GL._types``, which is a real file
    and always has been -- be declined without loading anything at all.
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

            # install() puts the real finder on sys.meta_path itself, so from
            # the next import onwards this one is not consulted at all.
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
