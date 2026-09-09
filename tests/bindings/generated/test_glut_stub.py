#! /usr/bin/env python3
"""``OpenGL.GLUT`` ships a stub, the way every other API namespace does.

GLUT is hand-maintained rather than registry-generated, so nothing emitted a
stub beside it, and ``from OpenGL.GLUT import *`` -- the documented way to use
it -- put no name a checker could see into the caller's namespace.  Every GLUT
program was therefore unchecked from its first line: ``glutInitDisplayMode``,
``GLUT_DOUBLE``, ``glutDisplayFunc`` and the rest were all undefined names.

The stub is generated from the declarations, not from what happened to load, so
it says the same thing on a machine with no GLUT library at all.
"""

import ast
import os

import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')
STUB = os.path.join(PACKAGE, 'GLUT', '__init__.pyi')


def declared():
    """{name: node} for everything the stub declares at module level."""
    if not os.path.exists(STUB):
        return {}
    with open(STUB, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=STUB)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found[node.name] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node
    return found


DECLARED = declared()

#: What a first GLUT program touches, across every shape the namespace holds:
#: a raw entry point, a freeglut one, a callback, a menu, a font pointer, and
#: constants from both the core set and freeglut's own.
ESSENTIALS = [
    'glutInit', 'glutInitDisplayMode', 'glutInitWindowSize', 'glutCreateWindow',
    'glutMainLoop', 'glutSwapBuffers', 'glutPostRedisplay', 'glutDestroyWindow',
    'glutDisplayFunc', 'glutKeyboardFunc', 'glutReshapeFunc', 'glutMouseFunc',
    'glutIdleFunc', 'glutTimerFunc', 'glutCreateMenu', 'glutAddMenuEntry',
    'glutBitmapCharacter', 'glutSolidSphere', 'glutWireTeapot',
    'glutMainLoopEvent', 'glutLeaveMainLoop', 'glutCloseFunc',
    'GLUT_BITMAP_HELVETICA_18', 'GLUT_STROKE_ROMAN',
    'GLUT_DOUBLE', 'GLUT_RGB', 'GLUT_DEPTH', 'GLUT_KEY_LEFT',
    'GLUT_ACTION_ON_WINDOW_CLOSE', 'GLUT_ACTION_CONTINUE_EXECUTION',
]


def test_the_stub_exists():
    assert os.path.exists(STUB), (
        'OpenGL/GLUT/__init__.pyi is missing, so every GLUT program is '
        'unchecked from its import line.'
    )


@pytest.mark.parametrize('name', ESSENTIALS)
def test_it_declares_what_a_program_reaches_for(name):
    assert name in DECLARED, '%s is not in the GLUT stub' % (name,)


def test_it_covers_the_namespace_the_package_offers():
    """Held against the runtime, so a declaration going missing is a failure.

    Skipped where GLUT is not installed: the comparison would then be against a
    namespace the machine could not build, not against the API.
    """
    glut = pytest.importorskip('OpenGL.GLUT')
    if not getattr(glut, 'glutInit', None):
        pytest.skip('no GLUT library on this machine')
    offered = {name for name in dir(glut)
               if name.startswith(('glut', 'GLUT_')) and not name.startswith('_')}
    missing = sorted(offered - set(DECLARED))
    assert not missing, (
        '%d name(s) the package offers are not in the stub: %s'
        % (len(missing), ', '.join(missing[:20]))
    )


def test_a_constant_is_an_int_and_an_entry_point_is_a_def():
    """The two shapes, so the stub is usable rather than merely present."""
    assert isinstance(DECLARED.get('GLUT_DOUBLE'), ast.AnnAssign)
    assert ast.unparse(DECLARED['GLUT_DOUBLE'].annotation) == 'int'
    assert isinstance(DECLARED.get('glutInitDisplayMode'), ast.FunctionDef)


def test_a_callback_setter_takes_the_callback():
    """``glutDisplayFunc(draw)`` is the whole point of the callback wrappers."""
    node = DECLARED.get('glutDisplayFunc')
    assert isinstance(node, ast.FunctionDef)
    arguments = node.args.posonlyargs + node.args.args
    assert len(arguments) == 1, 'glutDisplayFunc takes the callback and nothing else'


def test_an_unknown_name_does_not_error():
    """The namespace carries implementation leakage a caller may still touch."""
    with open(STUB, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=STUB)
    assert any(isinstance(node, ast.FunctionDef) and node.name == '__getattr__'
               for node in tree.body), (
        'without a module __getattr__ the stub makes every name it does not '
        'list an error, which is worse than having no stub.'
    )
