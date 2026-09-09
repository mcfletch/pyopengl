#! /usr/bin/env python3
"""A ``GLboolean`` parameter is stubbed as what a caller passes it.

``GL_TRUE`` and ``GL_FALSE`` are the values the specification names for these,
and they are what the documentation, the tutorials and every downstream program
pass.  They are ``IntConstant`` -- a subclass of ``int``, not of ``bool`` -- so
a stub saying ``bool`` makes the idiomatic call an error to a type checker while
accepting nothing extra: ``bool`` *is* an ``int``, so ``int`` covers ``True``
and ``GL_FALSE`` both.

The return side is the same annotation for a different reason: ``glIsTexture``
answers 0 or 1.
"""

import ast
import os

import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')

#: (module, entry point, parameter) for a spread of the GLboolean parameters:
#: a mask, a flag, the one every shader program calls, and one in a second API.
BOOLEAN_PARAMETERS = [
    ('GL/VERSION/GL_1_0', 'glColorMask', 'red'),
    ('GL/VERSION/GL_1_0', 'glDepthMask', 'flag'),
    ('GL/VERSION/GL_2_0', 'glVertexAttribPointer', 'normalized'),
    ('GL/VERSION/GL_3_0', 'glColorMaski', 'r'),
    ('GLES2/VERSION/GLES2_2_0', 'glVertexAttribPointer', 'normalized'),
]


def _annotation_of(relative, entry_point, parameter):
    path = os.path.join(PACKAGE, relative + '.pyi')
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == entry_point:
            for argument in node.args.posonlyargs + node.args.args:
                if argument.arg == parameter:
                    return ast.unparse(argument.annotation)
    return None


@pytest.mark.parametrize('relative,entry_point,parameter', BOOLEAN_PARAMETERS,
                         ids=['%s.%s' % (e, p) for _m, e, p in BOOLEAN_PARAMETERS])
def test_a_boolean_parameter_accepts_the_constants_named_for_it(
    relative, entry_point, parameter
):
    assert _annotation_of(relative, entry_point, parameter) == 'int', (
        '%s(%s=...) is passed GL_TRUE/GL_FALSE, which are int and not bool.'
        % (entry_point, parameter)
    )


def test_no_stub_declares_a_bool_parameter_anywhere():
    """The whole shipped surface, not only the sample above."""
    offenders = []
    for directory, folders, files in os.walk(PACKAGE):
        folders[:] = [f for f in folders if f != '__pycache__']
        for name in sorted(files):
            if not name.endswith('.pyi'):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding='utf-8') as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                for argument in node.args.posonlyargs + node.args.args:
                    if (argument.annotation is not None
                            and ast.unparse(argument.annotation) == 'bool'):
                        offenders.append('%s: %s(%s)'
                                         % (os.path.relpath(path, paths.ROOT),
                                            node.name, argument.arg))
    assert not offenders, (
        '%d parameter(s) stubbed as bool, which refuses GL_TRUE/GL_FALSE:\n%s'
        % (len(offenders), '\n'.join(offenders[:20]))
    )
