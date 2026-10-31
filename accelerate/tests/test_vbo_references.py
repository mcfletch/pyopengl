"""The accelerated VBO holds its array and its offsets hold their VBO by ordinary references."""
import gc
import sys

import numpy as np

from OpenGL.arrays import vbo


def test_an_array_assigned_to_data_outlives_the_buffer():
    """``data`` is a public attribute: an array put there is held like any other."""
    first = np.zeros(4, 'f')
    second = np.ones(4, 'f')
    third = np.full(2, 2.0, 'f')
    counts = [sys.getrefcount(item) for item in (first, second, third)]
    buffer = vbo.VBO(first)
    buffer.data = second
    buffer.set_array(third)
    buffer.data = second
    del buffer
    gc.collect()
    assert [sys.getrefcount(item) for item in (first, second, third)] == counts


def test_an_offset_holds_its_buffer_and_lets_it_go():
    data = np.zeros(4, 'f')
    buffer = vbo.VBO(data)
    count = sys.getrefcount(buffer)
    offset = buffer + 8
    assert offset.offset == 8 and offset.vbo is buffer
    offset.vbo = vbo.VBO(np.zeros(2, 'f'))
    offset.vbo = buffer
    del offset
    gc.collect()
    assert sys.getrefcount(buffer) == count
