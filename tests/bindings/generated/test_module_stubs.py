#! /usr/bin/env python3
"""Every friendly module ships a stub saying what is in it.

A friendly module fills its namespace from the declaration tables when it is
imported -- ``_define(globals(), 'OpenGL.raw.GL.ARB.vertex_array_object')`` --
and nothing reading the file can follow that.  Without a stub beside it an
editor offers no completion in the module and a checker types every name in it
as ``Any``, which is what the generated files used to provide by existing.

These check the shipped stubs against the modules they describe, so a
regeneration that stopped emitting them, or a module whose stub went stale, is
a failure here rather than a report from somebody's editor.
"""

import ast
import os

import paths
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT
PACKAGE = os.path.join(ROOT, 'OpenGL')

#: A spread: a core version, two extensions, and a second API namespace.
SAMPLE = [
    'GL/VERSION/GL_1_1',
    'GL/ARB/vertex_array_object',
    'GL/ARB/shader_objects',
    'GLES2/VERSION/GLES2_2_0',
]


def _source_for(module_name):
    """The file a checker reads for `module_name`: its stub, or its source."""
    relative = os.path.join(*module_name.split('.')[1:])
    for candidate in (relative + '.pyi', relative + '.py'):
        path = os.path.join(PACKAGE, candidate)
        if os.path.exists(path):
            return path
    return None


def visible_names(module_name, seen=None):
    """Every name a checker sees in `module_name`, re-exports included.

    ``from X import *`` in a stub re-exports what X has, which is how a version
    module offers the one below it and how every module offers the GL types.
    Following it is what makes this compare like with like.
    """
    seen = seen if seen is not None else set()
    if module_name in seen:
        return set()
    seen.add(module_name)
    path = _source_for(module_name)
    if path is None:
        return set()
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    names = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == '*':
                    names |= visible_names(node.module, seen)
                else:
                    names.add(alias.asname or alias.name)
    return names


def stub_names(relative):
    """What the stub beside `relative` gives a checker."""
    module_name = 'OpenGL.%s' % (relative.replace('/', '.'),)
    if not os.path.exists(os.path.join(PACKAGE, relative + '.pyi')):
        pytest.fail('no stub beside OpenGL/%s.py' % (relative,))
    return visible_names(module_name)


@pytest.mark.parametrize('relative', SAMPLE)
def test_a_module_has_a_stub_naming_its_entry_points(relative):
    """The names the module ends up with are the names the stub declares."""
    module = __import__(
        'OpenGL.%s' % (relative.replace('/', '.'),), {}, {}, ['*']
    )
    declared = stub_names(relative)
    live = {
        name
        for name in dir(module)
        if name.startswith(('gl', 'GL', 'egl', 'EGL', 'wgl', 'glX'))
        and not name.startswith('_')
    }
    missing = sorted(live - declared)
    assert not missing, (
        'OpenGL/%s.py defines names its stub does not: %s'
        % (relative, ', '.join(missing[:10]))
    )


def test_every_generated_module_has_one():
    """Not a sample: a module without a stub is a module with no completion."""
    from OpenGL import _declarations

    without = []
    for name in _declarations.data_declarations().module_names():
        parts = name.split('.')
        if len(parts) < 4 or parts[1] != 'raw':
            continue
        relative = os.path.join(*parts[2:])
        if not os.path.exists(os.path.join(PACKAGE, relative + '.py')):
            continue  # a generated module with no friendly module above it
        if not os.path.exists(os.path.join(PACKAGE, relative + '.pyi')):
            without.append(relative)
    assert not without, 'modules with no stub: %s' % (', '.join(without[:10]),)


def test_the_shared_aliases_are_beside_the_package():
    """The stubs name their array types out of one file rather than each
    declaring them, so that file has to be there."""
    assert os.path.exists(os.path.join(PACKAGE, '_typing.pyi'))


def test_a_stub_only_module_is_not_importable():
    """``OpenGL._typing`` describes types; it is not a module to import.

    Named here because a stub-only module looks like a missing file to anyone
    who has not met one, and because ``from OpenGL._typing import ...`` in
    real code would be an ImportError at run time.
    """
    with pytest.raises(ImportError):
        __import__('OpenGL._typing')
