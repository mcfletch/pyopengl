"""How the C layer is told which ``OpenGL.arrays`` class each element uses.

The C element table names its array class -- ``"GLubyteArray"`` -- and resolves
that name against a mapping the Python side hands it at configure time. It fills
its own table in its own order, so the two sides share a *name* and never an
index.

They used to share a position: Python passed a list built from a generated
``ARRAY_TYPES``, and the C read it at a compile-time index. Adding an element
type shifted every index after it, so a tree whose Python was newer than its
built extension handed out the wrong class -- ``GLubyteArray`` came back as
``GLshortArray``, and a 64-byte ``glGetBufferSubData`` returned 128. No error;
the failure surfaced three call frames away, on a reshape.
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
    """The whole point of resolving by name: what used to be a wrong answer is
    now a refusal that names the class and says what to do."""

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
