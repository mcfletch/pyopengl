"""``OpenGL.arrays.vbo.VBO`` is a class to a type checker, as it is at run time.

The module binds ``VBO`` and its three companions to OpenGL_accelerate's
classes where the accelerator loads, and to its own Python classes where it
does not. A checker cannot run that choice, so it reads whatever the source
makes of it without running anything: a ``VBO = None`` placeholder makes every
``vbo.VBO(data)`` in a caller's code a call of ``None``. The Python classes are
the ones a checker has to see, since the accelerated ones carry no declarations.
"""

import ast
import inspect

import pytest

from OpenGL.arrays import vbo

CLASSES = ('VBO', 'VBOOffset', 'VBOHandler', 'VBOOffsetHandler')


def checker_reads(source):
    """The names ``source`` binds at module level as a type checker reads them.

    Maps each name to ``'class'`` or to the source of the value assigned to it,
    following the branches of a top-level ``if`` that a checker takes: the
    body where the test holds with ``TYPE_CHECKING`` true, the ``else``
    otherwise. The first binding of a name is the one a checker keeps.
    """
    bound = {}

    def walk(statements):
        for statement in statements:
            if isinstance(statement, ast.ClassDef):
                bound.setdefault(statement.name, 'class')
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        bound.setdefault(target.id, ast.unparse(statement.value))
            elif isinstance(statement, ast.If):
                walk(statement.body if _holds_for_a_checker(statement.test)
                     else statement.orelse)

    walk(ast.parse(source).body)
    return bound


def _holds_for_a_checker(test):
    """Whether a checker takes the body of an ``if`` with this test."""
    if isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING':
        return True
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        return any(_holds_for_a_checker(value) for value in test.values)
    return False


@pytest.mark.parametrize('name', CLASSES)
def test_a_checker_reads_the_python_class(name):
    assert checker_reads(inspect.getsource(vbo))[name] == 'class'


def test_the_reader_follows_the_branch_a_checker_takes():
    source = (
        'VBO = None\n'
        'if TYPE_CHECKING or accelerated is None:\n'
        '    class VBOOffset: pass\n'
        'else:\n'
        '    VBOOffset = accelerated.VBOOffset\n'
        'if accelerated:\n'
        '    VBOHandler = accelerated.VBOHandler\n'
    )
    assert checker_reads(source) == {'VBO': 'None', 'VBOOffset': 'class'}
