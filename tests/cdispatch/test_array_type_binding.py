"""How the C layer is told which ``OpenGL.arrays`` class each element uses.

The C element table names its array class -- ``"GLubyteArray"`` -- and resolves
that name against a mapping the Python side hands it at configure time. It fills
its own table in its own order, so the two sides share a *name* and never an
index.

A shared *position* cannot survive an element type being added: every index
after it moves, so a tree whose Python is newer than its built extension
converts with the wrong class. That is a wrong answer rather than a crash --
``GLubyteArray`` answering as ``GLshortArray`` makes a 64-byte
``glGetBufferSubData`` return 128 -- and it surfaces call frames away from the
cause. A name survives it, which is why the name is what crosses.
"""

import os
import re
import subprocess
import sys
import textwrap

import pytest

from OpenGL._dispatch import support

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ELEMENTS = os.path.join(ROOT, 'accelerate', 'src', 'c', 'generated',
                        'pygl_elements.h')


def generated_class_names():
    """Every array class the generated element table names."""
    if not os.path.exists(ELEMENTS):
        pytest.skip('the generated element table is not in this tree')
    with open(ELEMENTS, encoding='utf-8') as handle:
        text = handle.read()
    return sorted(set(re.findall(r'"(\w+Array|ArrayDatatype)"', text)))


class TestTheMappingIsByName:
    def test_it_answers_for_every_class_the_table_names(self):
        """The C resolves each of these at configure time; one it cannot find
        is an entry point that would convert with the wrong class, or crash."""
        mapping = support.array_type_map()
        missing = [name for name in generated_class_names()
                   if name not in mapping]
        assert missing == []

    def test_every_value_is_an_array_class(self):
        for name, value in support.array_type_map().items():
            assert hasattr(value, 'asArray'), name

    def test_it_is_keyed_by_the_name_the_c_table_carries(self):
        mapping = support.array_type_map()
        from OpenGL import arrays

        assert mapping['GLubyteArray'] is arrays.GLubyteArray
        assert mapping['GLuintArray'] is arrays.GLuintArray

    def test_the_classes_added_for_pointer_sized_integers_are_in_it(self):
        """The ones whose addition shifted the old positional table."""
        mapping = support.array_type_map()
        assert 'GLintptrArray' in mapping
        assert 'GLsizeiptrArray' in mapping

    def test_two_names_for_one_class_both_answer(self):
        """``EGLAttribArray`` is ``GLintArray`` under another name, and the
        table may carry either."""
        from OpenGL import arrays

        mapping = support.array_type_map()
        assert mapping['EGLAttribArray'] is arrays.EGLAttribArray


class TestAClassTheBuildNeedsAndCannotFind:
    """Resolving by name makes this a refusal that names the class and says
    what to do, where an index would quietly answer with the wrong one."""

    def test_configure_refuses_a_mapping_that_is_missing_one(self):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch layer is not built')
        # In a child, because configure() sets process-wide state.  Through
        # the real configure(), so this is the call production makes.
        script = textwrap.dedent("""
            from OpenGL._dispatch import support

            complete = support.array_type_map
            support.array_type_map = lambda: {
                name: value for name, value in complete().items()
                if name != 'GLubyteArray'
            }
            import OpenGL._dispatch as dispatch
            try:
                dispatch.configure()
            except Exception as error:
                print(type(error).__name__, error)
            else:
                print('accepted')
        """)
        completed = subprocess.run(
            [sys.executable, '-c', script], capture_output=True, text=True,
            check=False)
        assert 'GLubyteArray' in completed.stdout, completed
        assert 'accepted' not in completed.stdout, completed


class TestNothingSharesAPosition:
    def test_the_generated_tables_no_longer_publish_an_ordered_list(self):
        """A positional table nothing reads is a trap for whoever reads it
        next."""
        from OpenGL._dispatch import _tables

        assert not hasattr(_tables, 'ARRAY_TYPES')
