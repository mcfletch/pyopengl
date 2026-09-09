#! /usr/bin/env python3
"""A constant is the same type wherever the package declares it.

``GL_BYTE`` is declared twice: the generated ``OpenGL/GL/__init__.pyi`` says
``int``, and ``OpenGL/raw/GL/_types.py`` -- which every generated extension stub
star-imports -- holds the value itself.  Both are describing one ``IntConstant``,
which *is* an ``int``.

Two answers to that is a false error in a user's program rather than a
cosmetic difference, because star imports are how these modules are used::

    from OpenGL.GL import *
    from OpenGL.GL.ARB.occlusion_query import *   # 15 "Incompatible import of"

The second line re-exports the raw module's names over the first line's, and a
checker compares the two declarations at that point.
"""

import ast
import os

import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')

#: Every raw ``_types`` module.  Only the GL one defines these constants; the
#: GLES ones reach them by star-importing along the chain, so annotating the
#: first settles all four -- and the second case below holds the rest to it if
#: one ever grows a constant of its own.
RAW_TYPES = ['raw/GL/_types.py', 'raw/GLES1/_types.py',
             'raw/GLES2/_types.py', 'raw/GLES3/_types.py']

#: The raw module the constants are defined in, and the generated stub whose
#: declarations of the same names it has to agree with.
PAIRINGS = [('raw/GL/_types.py', 'GL/__init__.pyi')]


def _declared_types(relative):
    """{name: annotation} for every annotated module-level GL constant."""
    path = os.path.join(PACKAGE, relative)
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    found = {}
    for node in tree.body:
        if (isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id.startswith('GL_')):
            found[node.target.id] = ast.unparse(node.annotation)
    return found


@pytest.mark.parametrize('source,stub', PAIRINGS, ids=[s for s, _t in PAIRINGS])
def test_the_raw_module_and_the_stub_declare_a_constant_alike(source, stub):
    if not os.path.exists(os.path.join(PACKAGE, source)):
        pytest.skip('%s has no raw _types module' % (source,))
    raw = _declared_types(source)
    generated = _declared_types(stub)
    shared = sorted(set(raw) & set(generated))
    assert shared, (
        '%s declares the type of none of the constants in it, so a stub that '
        'star-imports it re-exports whatever a checker infers.' % (source,)
    )
    disagreements = ['%s: %s says %s, %s says %s'
                     % (name, source, raw[name], stub, generated[name])
                     for name in shared if raw[name] != generated[name]]
    assert not disagreements, '\n'.join(disagreements)


@pytest.mark.parametrize('source', RAW_TYPES)
def test_every_constant_the_raw_module_defines_says_what_it_is(source):
    """An unannotated one is inferred as ``Constant``, which is not an ``int``."""
    path = os.path.join(PACKAGE, source)
    if not os.path.exists(path):
        pytest.skip('%s has no raw _types module' % (source,))
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    bare = [target.id
            for node in tree.body if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id.startswith('GL_')
            and isinstance(node.value, ast.Call)
            and ast.unparse(node.value.func).endswith('Constant')]
    assert not bare, (
        '%s: %s carry no annotation, so a checker reads them as Constant '
        'rather than as the int each one is.' % (source, ', '.join(bare))
    )
