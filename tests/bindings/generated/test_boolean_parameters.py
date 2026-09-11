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
import stubs

PACKAGE = paths.PACKAGE

#: (module, entry point, parameter) for a spread of the GLboolean parameters:
#: a mask, a flag, the one every shader program calls, and one in a second API.
BOOLEAN_PARAMETERS = [
    ('GL/VERSION/GL_1_0', 'glColorMask', 'red'),
    ('GL/VERSION/GL_1_0', 'glDepthMask', 'flag'),
    ('GL/VERSION/GL_2_0', 'glVertexAttribPointer', 'normalized'),
    ('GL/VERSION/GL_3_0', 'glColorMaski', 'r'),
    ('GLES2/VERSION/GLES2_2_0', 'glVertexAttribPointer', 'normalized'),
]


@pytest.mark.parametrize('relative,entry_point,parameter', BOOLEAN_PARAMETERS,
                         ids=['%s.%s' % (e, p) for _m, e, p in BOOLEAN_PARAMETERS])
def test_a_boolean_parameter_accepts_the_constants_named_for_it(
    relative, entry_point, parameter
):
    assert stubs.parameter_annotation(
        relative + '.pyi', entry_point, parameter) == 'int', (
        '%s(%s=...) is passed GL_TRUE/GL_FALSE, which are int and not bool.'
        % (entry_point, parameter)
    )


def test_no_stub_declares_a_bool_parameter_anywhere():
    """The whole shipped surface, not only the sample above."""
    offenders = []
    for relative in stubs.every_stub():
        for name, node in stubs.functions(relative).items():
            for argument in stubs.parameters(node):
                if (argument.annotation is not None
                        and ast.unparse(argument.annotation) == 'bool'):
                    offenders.append('%s: %s(%s)'
                                     % (relative, name, argument.arg))
    assert not offenders, (
        '%d parameter(s) stubbed as bool, which refuses GL_TRUE/GL_FALSE:\n%s'
        % (len(offenders), '\n'.join(offenders[:20]))
    )
