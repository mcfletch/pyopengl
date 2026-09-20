#! /usr/bin/env python3
"""``MODULE_ANNOTATIONS`` says where a name is defined, and has to be right.

The flag exists for the documentation generators: with it set, a constant and
an alternate carry a ``__module__`` naming the module that declares them, and
``directdocs/dumbpydoc.py`` uses that to put each name on one page rather than
on every page that re-exports it.

The answer has to come from the declaration tables rather than from wherever
the object happened to be constructed.  :class:`OpenGL.constant.Constant`
guesses from the calling frame, which works while a module builds its own
constants and stops working the moment one loader builds them all -- and it
stops working silently, since a wrong module name looks like any other module
name.  So these ask the question directly.
"""

import json

import pytest

from childenv import json_from_child

REPORT = '''
import json
import OpenGL
OpenGL.MODULE_ANNOTATIONS = True
from OpenGL import GL
from OpenGL.GL.ARB import vertex_buffer_object as vbo
import OpenGL.raw.GL.VERSION.GL_1_1 as raw11

print(json.dumps({
    "GL_TRIANGLES": getattr(GL.GL_TRIANGLES, "__module__", None),
    "GL_TRIANGLES_raw": getattr(raw11.GL_TRIANGLES, "__module__", None),
    "GL_ARRAY_BUFFER_ARB": getattr(
        vbo.GL_ARRAY_BUFFER_ARB, "__module__", None
    ),
    "glBegin": getattr(GL.glBegin, "__module__", None),
}))
'''


@pytest.fixture(scope='module')
def annotated():
    return json_from_child(REPORT)


def test_a_core_constant_names_the_version_that_declares_it(annotated):
    """``GL_TRIANGLES`` is OpenGL 1.0's, wherever it is imported from."""
    assert annotated['GL_TRIANGLES'] == 'OpenGL.raw.GL.VERSION.GL_1_0'


def test_the_raw_module_agrees_with_the_friendly_one(annotated):
    """Re-exporting a constant does not move where it was declared.

    ``GL_1_1`` and ``OpenGL.GL`` both offer ``GL_TRIANGLES``; both are passing
    on ``GL_1_0``'s, and both say so.
    """
    assert annotated['GL_TRIANGLES_raw'] == annotated['GL_TRIANGLES']


def test_an_extension_constant_names_the_extension(annotated):
    """A constant an extension introduced is the extension's, not the core's."""
    assert annotated['GL_ARRAY_BUFFER_ARB'] == (
        'OpenGL.raw.GL.ARB.vertex_buffer_object'
    )


def test_an_entry_point_names_the_version_that_declares_it(annotated):
    """Entry points answer the same question the same way."""
    assert annotated['glBegin'] == 'OpenGL.raw.GL.VERSION.GL_1_0'


def test_the_flag_is_off_by_default():
    """Nothing is annotated in a run that did not ask, since the walk and the
    attribute cost something on every constant built."""
    answered = json_from_child(
        'import json\n'
        'from OpenGL import GL, _configflags\n'
        'print(json.dumps({"flag": bool(_configflags.MODULE_ANNOTATIONS)}))\n'
    )
    assert answered['flag'] is False
