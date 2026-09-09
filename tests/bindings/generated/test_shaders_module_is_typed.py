#! /usr/bin/env python3
"""``OpenGL.GL.shaders`` says what it takes and what it answers.

``compileShader`` and ``compileProgram`` are what a modern GL program calls to
get a program name, and a name flows straight into ``glUseProgram``,
``glGetUniformLocation`` and every uniform setter.  Unannotated, both answer
``Any``, so a checker follows that ``Any`` through the whole of a caller's
shader handling and has nothing to say about any of it -- including where the
program is later confused with a shader, or with a texture.

Held here rather than in a stub because the module is hand-written: the
annotations belong on the code, where they are read alongside it.
"""

import ast
import inspect
import os
import textwrap

import pytest

from OpenGL.GL import shaders

#: The module's own entry points -- what ``__all__`` names that is defined here
#: rather than re-exported from the generated modules.
DECLARED = ['compileShader', 'compileProgram']


@pytest.mark.parametrize('name', DECLARED)
def test_it_says_what_it_answers(name):
    signature = inspect.signature(getattr(shaders, name))
    assert signature.return_annotation is not inspect.Signature.empty, (
        '%s answers a GL name that flows into every later call; unannotated it '
        'answers Any, and the checker loses the caller from there on.' % (name,)
    )


@pytest.mark.parametrize('name', DECLARED)
def test_it_says_what_it_takes(name):
    signature = inspect.signature(getattr(shaders, name))
    bare = [parameter.name for parameter in signature.parameters.values()
            if parameter.annotation is inspect.Parameter.empty]
    assert not bare, '%s(%s) carry no annotation' % (name, ', '.join(bare))


def test_a_program_is_an_int_a_caller_can_pass_to_gl():
    """``ShaderProgram`` subclasses ``int``, which is what the stubs expect."""
    assert issubclass(shaders.ShaderProgram, int)


def test_every_method_on_a_program_is_annotated():
    """It is a context manager and a validator, not only a number."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(shaders.ShaderProgram)))
    bare = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.returns is None:
            bare.append('%s -> ?' % (node.name,))
        bare += ['%s(%s)' % (node.name, argument.arg)
                 for argument in node.args.args
                 if argument.arg != 'self' and argument.annotation is None]
    assert not bare, ', '.join(bare)


def test_the_module_is_not_excluded_from_checking():
    """A ``# mypy: ignore-errors`` header would make the annotations decorative."""
    path = inspect.getsourcefile(shaders)
    assert path is not None
    with open(path, encoding='utf-8') as handle:
        head = handle.read(4096)
    assert 'mypy: ignore-errors' not in head, (
        '%s is excluded from checking, so nothing holds its annotations to its '
        'body.' % (os.path.basename(path),)
    )
