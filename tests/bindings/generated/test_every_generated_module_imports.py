#! /usr/bin/env python3
"""Every module the package ships can be imported.

The friendly modules fill their namespaces from the declaration tables when
they are imported, so importing one is the only way to find out whether the
tables it names are there.  A module whose ``from OpenGL.raw.X import _types``
has nothing to import raises ``ImportError`` at the first line a user writes,
and nothing else in the suite goes near it: the entry-point tests reach a
module through the API namespace, which does not enumerate what it failed to
load.

That is not hypothetical.  ``OpenGL/raw/GLSC2/_types.py`` is absent where every
other API has one, and eight of the twelve GLSC2 modules raise on import
because of it.
"""

import importlib
import os
import pkgutil

import paths
import pytest
from backends import egl_refusal, missing_library

#: The API namespaces, each imported on its own so a failure names the one it
#: is in rather than stopping at the first.
NAMESPACES = ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'GLU', 'GLX', 'WGL',
              'EGL')


def _modules_under(namespace):
    """Every module below ``OpenGL.<namespace>``, by name."""
    package = importlib.import_module('OpenGL.%s' % (namespace,))
    return sorted(
        found.name
        for found in pkgutil.walk_packages(package.__path__,
                                           'OpenGL.%s.' % (namespace,))
    )


def _collect():
    found = []
    refused = egl_refusal()
    for namespace in NAMESPACES:
        if namespace == 'EGL' and refused is not None:
            # No EGL library here, and the binding refuses to import without
            # one -- which is what it promises.  A machine that has one walks
            # this namespace.
            found.append(pytest.param(
                'OpenGL.EGL', id='OpenGL.EGL',
                marks=pytest.mark.skip(
                    reason='OpenGL.EGL does not import here: %s' % (refused,)),
            ))
            continue
        try:
            found.extend(_modules_under(namespace))
        except ImportError as error:      # the namespace itself is broken
            found.append(('OpenGL.%s' % (namespace,), error))
    return found


MODULES = _collect()


def test_the_walk_found_the_modules():
    """A walk that found nothing would make every case below vacuous."""
    assert len(MODULES) > 1000


@pytest.mark.parametrize('name', MODULES, ids=lambda name: str(name))
def test_a_shipped_module_imports(name):
    if not isinstance(name, str):
        pytest.fail('OpenGL.%s could not be walked: %s' % name)
    try:
        importlib.import_module(name)
    except ImportError as error:
        if missing_library(name, error):
            # A module that needs a library this machine lacks, saying so the
            # way it promises to (backends.OPTIONAL_MODULES).
            pytest.skip(str(error))
        pytest.fail(
            '%s does not import: %s\n'
            'A module that raises here is one a user cannot reach at all.'
            % (name, error)
        )


def test_every_api_that_imports_a_types_module_has_one():
    """``_types`` is imported by name, so its absence is an ImportError.

    Checked separately from the walk above because it says *what* is missing
    rather than which module noticed first.  Only the namespaces that actually
    import one are held to having it: GLU declares its constants in
    ``raw/GLU/constants.py`` and reads its types from GL, so it needs none.
    """
    raw = os.path.join(paths.ROOT, 'OpenGL', 'raw')
    wanted = set()
    for directory, folders, files in os.walk(os.path.join(paths.ROOT, 'OpenGL')):
        folders[:] = [name for name in folders if name != '__pycache__']
        for name in files:
            if not name.endswith('.py'):
                continue
            with open(os.path.join(directory, name), encoding='utf-8') as handle:
                text = handle.read()
            for namespace in NAMESPACES:
                if 'from OpenGL.raw.%s import' % (namespace,) in text \
                        and '_types' in text:
                    wanted.add(namespace)
    missing = sorted(
        namespace for namespace in wanted
        if not os.path.exists(os.path.join(raw, namespace, '_types.py'))
    )
    assert not missing, (
        'imported by name but absent -- no OpenGL/raw/<api>/_types.py for: %s'
        % (', '.join(missing),)
    )
