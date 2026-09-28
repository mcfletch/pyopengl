"""``OpenGL.arrays.vbo`` answers its own classes where the accelerator has no VBO

``acceleratesupport`` says whether PyOpenGL_accelerate is installed at all.
Whether *its* ``vbo`` module imports is a second question: a partial install,
or an extension module that will not load on this interpreter, leaves the rest
of the accelerator working and that one absent.  The answer is the Python
implementation and a warning, rather than an ``ImportError`` out of ``import
OpenGL.arrays.vbo``.
"""

import logging
import sys
import types

from OpenGL import acceleratesupport
from OpenGL.arrays import vbo


class TestTheAcceleratorsVBOIsOptional:
    def test_an_accelerator_without_one_answers_none(self, monkeypatch, caplog):
        monkeypatch.setattr(acceleratesupport, 'ACCELERATE_AVAILABLE', True)
        monkeypatch.setitem(
            sys.modules, 'OpenGL_accelerate', types.ModuleType('OpenGL_accelerate')
        )
        # ``from package import name`` answers an already-imported submodule
        # even where the package object has no such attribute, so the real one
        # has to be out of the way for the stand-in to be the whole answer.
        monkeypatch.delitem(sys.modules, 'OpenGL_accelerate.vbo', raising=False)
        with caplog.at_level(logging.WARNING, logger='OpenGL.arrays.vbo'):
            assert vbo._accelerated() is None
        assert 'VBO accelerator' in caplog.text

    def test_it_is_not_asked_for_where_the_accelerator_is_absent(self, monkeypatch):
        """No import is attempted, so nothing is logged about one failing."""
        monkeypatch.setattr(acceleratesupport, 'ACCELERATE_AVAILABLE', False)
        assert vbo._accelerated() is None
