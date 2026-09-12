#! /usr/bin/env python3
"""Every module the package ships compiles without a warning.

The generator writes each extension's registry documentation into the module's
docstring, and a docstring is a string: a backslash in the prose is an escape
sequence, and one Python does not recognise is a ``SyntaxWarning``.  ASCII
diagrams are where this lands, since they are drawn with backslashes.

It reaches further than the noise on one import.  A distribution's own build
runs Python over the installed tree and prints the warning into an ``apt
upgrade``; a caller running under ``-W error`` gets an exception out of
``import OpenGL``; and a warning nobody can act on trains every reader to
ignore the ones they could.

Compiled from the file's own bytes rather than imported, because the warning is
raised while the source is turned into bytecode and a cached ``.pyc`` means
nothing raises it a second time.  That is also why the tree can be clean on a
developer's machine and warn on a user's: the developer's is warm.

https://github.com/mcfletch/pyopengl/issues/143
https://github.com/mcfletch/pyopengl/issues/158
"""

import pathlib
import warnings

import paths
import pytest

#: The installed package, as a user receives it.
PACKAGE = pathlib.Path(paths.PACKAGE)


def _shipped_modules():
    return sorted(PACKAGE.rglob('*.py'))


def _compile_warnings(path):
    """Every warning raised turning `path` into bytecode."""
    source = path.read_bytes()
    with warnings.catch_warnings(record=True) as raised:
        warnings.simplefilter('always')
        compile(source, str(path), 'exec')
    return [f'{one.category.__name__}: {one.message}' for one in raised]


def test_there_are_modules_to_check():
    """A glob that found nothing would pass the case below saying nothing."""
    assert len(_shipped_modules()) > 100, PACKAGE


def test_no_shipped_module_warns_while_compiling():
    offenders = []
    for path in _shipped_modules():
        for warning in _compile_warnings(path):
            offenders.append(f'{path.relative_to(PACKAGE)}: {warning}')
    assert not offenders, '\n'.join(
        [f'{len(offenders)} module(s) warn while compiling:'] + offenders[:40]
    )


@pytest.mark.parametrize('name', ['GL/AMD/vertex_shader_tessellator.py'])
def test_the_reported_module_compiles_clean(name):
    """The one the tickets name, so a regression there is named rather than
    counted among however many the case above found."""
    path = PACKAGE / name
    if not path.exists():
        pytest.skip(f'{name} is not in this build')
    assert _compile_warnings(path) == []
