#! /usr/bin/env python3
"""That every package PyOpenGL ships is a package with something in it.

Two shapes import without error and carry nothing, and both hide from the
tools that go looking:

*An empty package.*  A directory whose ``__init__.py`` is empty and which
holds no other module.  ``import OpenGL.X`` succeeds, ``dir()`` is bare, and a
reader takes the import as evidence that the API is bound.

*An implicit namespace package.*  A directory with modules in it and no
``__init__.py`` at all.  Python 3 imports it, but the name resolves to a
namespace with nothing of the package's own in it, and
``pkgutil.walk_packages`` does not descend into it -- so the modules beneath
are reachable only by their full dotted names, and the documentation
generator, which walks, reports the API as absent.
"""

import os

import paths
import pytest

#: The package directory under test.
PACKAGE = os.path.join(paths.ROOT, 'OpenGL')

#: Directories that are data or build output rather than source.
SKIP_DIRECTORIES = {'__pycache__', 'DLLS', 'tests'}


def _package_directories():
    """Every directory under ``OpenGL`` that holds Python source."""
    for directory, subdirectories, names in os.walk(PACKAGE):
        subdirectories[:] = [
            name for name in subdirectories if name not in SKIP_DIRECTORIES
        ]
        if any(name.endswith(('.py', '.pyi')) for name in names):
            yield directory


def _relative(directory):
    return os.path.relpath(directory, paths.ROOT)


@pytest.mark.parametrize(
    'directory', sorted(_package_directories()), ids=_relative
)
def test_the_directory_is_a_package(directory):
    """A directory of modules with no ``__init__.py`` is walked into by nothing."""
    assert os.path.isfile(os.path.join(directory, '__init__.py')), (
        '%s holds modules and has no __init__.py, so it imports as a '
        'namespace package: pkgutil.walk_packages will not enter it and the '
        'modules in it are documented nowhere' % (_relative(directory),)
    )


@pytest.mark.parametrize(
    'directory', sorted(_package_directories()), ids=_relative
)
def test_the_package_is_not_empty(directory):
    """An importable package with nothing in it says an API is bound when it is not."""
    initialiser = os.path.join(directory, '__init__.py')
    if not os.path.isfile(initialiser):
        pytest.skip('reported by test_the_directory_is_a_package')
    if os.path.getsize(initialiser):
        return
    siblings = [
        name for name in os.listdir(directory)
        if name.endswith(('.py', '.pyi')) and name != '__init__.py'
    ]
    subpackages = [
        name for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name))
        and name not in SKIP_DIRECTORIES
    ]
    assert siblings or subpackages, (
        '%s is an empty package: it imports, and there is nothing in it'
        % (_relative(directory),)
    )
