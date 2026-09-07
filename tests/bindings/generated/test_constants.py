#! /usr/bin/env python3
"""``OpenGL.constant.Constant``: a number that remembers what it is called.

Every ``GL_*`` name is one of these rather than a plain int, so that a value
printed in an error message or a log says which enum it was.  That makes it a
type a caller can end up storing, and a stored value has to survive being
written out and read back -- a program caching a display list or a material
description alongside the enum it was built with is doing exactly that.
"""

import pickle
import unittest

from OpenGL.constant import Constant
from OpenGL.GL import GL_TRIANGLES, GL_VERTEX_ARRAY


class TestAConstantIsANumber:
    def test_it_compares_equal_to_its_value(self):
        assert GL_VERTEX_ARRAY == 0x8074
        assert GL_TRIANGLES == 0x0004

    def test_it_carries_the_name_it_was_declared_with(self):
        assert GL_VERTEX_ARRAY.name == 'GL_VERTEX_ARRAY'


class TestAConstantSurvivesAPickle:
    """Both the value and the name, since the name is why it is not an int."""

    def test_the_value_comes_back(self):
        restored = pickle.loads(pickle.dumps(GL_VERTEX_ARRAY))
        assert restored == GL_VERTEX_ARRAY, (restored, GL_VERTEX_ARRAY)

    def test_the_name_comes_back(self):
        restored = pickle.loads(pickle.dumps(GL_VERTEX_ARRAY))
        assert restored.name == GL_VERTEX_ARRAY.name, restored.name

    def test_every_protocol_round_trips_it(self):
        """A stored value outlives the interpreter that wrote it."""
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            restored = pickle.loads(pickle.dumps(GL_TRIANGLES, protocol))
            assert restored == GL_TRIANGLES, (protocol, restored)
            assert restored.name == GL_TRIANGLES.name, (protocol, restored.name)

    def test_one_made_by_hand_round_trips_too(self):
        made = Constant('GL_SOMETHING_MADE_UP', 0x1234)
        restored = pickle.loads(pickle.dumps(made))
        assert restored == 0x1234
        assert restored.name == 'GL_SOMETHING_MADE_UP'


if __name__ == '__main__':
    unittest.main()
