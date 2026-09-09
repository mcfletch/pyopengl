#! /usr/bin/env python3
"""Every generated module tells a checker not to read it.

``py.typed`` promises the package can be analysed, and a downstream checker
keeps that promise: without the marker a user's own report fills with errors
from files they never wrote.  The generated modules cannot honour the promise
-- their names arrive from the declaration tables when ``_define()`` runs, so a
checker reading the source sees a module that defines almost nothing and calls
a great many things that are not there.  The typed surface is the ``.pyi`` stub
beside each package.

``src/mark_generated_untyped.py`` puts the marker in.  A generator that writes
its own header will strip it out again on the next regeneration, and nothing
about the result looks wrong: the file still imports, the suite still passes,
and the errors appear only in a checker run nobody had wired up.  That is what
happened to the eight ``_glgets.py`` tables, and this is what would have said
so.
"""

import os

import mark_generated_untyped
import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')


def generated_modules():
    """Every module the marking tool considers machine-written."""
    found = []
    for directory, folders, files in os.walk(PACKAGE):
        folders[:] = [name for name in folders if name != '__pycache__']
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
            # The tool's own rule, imported rather than restated: a test that
            # disagreed with it would pass while the tool did nothing.
            if mark_generated_untyped.generated(path, text):
                found.append((os.path.relpath(path, paths.ROOT), text))
    return found


MODULES = generated_modules()


def test_there_are_generated_modules_to_check():
    """A walk that found nothing would make every case below vacuous."""
    assert len(MODULES) > 1000


@pytest.mark.parametrize('relative,text',
                         MODULES, ids=[relative for relative, _ in MODULES])
def test_a_generated_module_carries_the_marker(relative, text):
    assert text.startswith(mark_generated_untyped.MARKER), (
        '%s is generated but does not start with %r. If a generator writes '
        'this file\'s header, the marker belongs in that header -- otherwise '
        'the next regeneration removes it again.'
        % (relative, mark_generated_untyped.MARKER)
    )
