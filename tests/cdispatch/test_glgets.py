"""The output-size table keyed on a pname argument.

285 of the friendly layer's ``setOutput`` calls size their output array by
looking the pname up in ``_glget_size_mapping``.  In C that is a static sorted
table and a binary search; the shape matters as well as the count, because
``glGetFloatv(GL_MODELVIEW_MATRIX)`` hands back a 4x4 array rather than 16
numbers.
"""

import os

import pytest

from cdispatch import glgets

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')


@pytest.fixture(scope='module')
def table():
    return glgets.read_table(os.path.join(PACKAGE, 'raw', 'GL', '_glgets.py'))


class TestReading:
    def test_reads_the_common_scalar_case(self, table):
        assert table[0x8B89].shape == (1,)  # GL_ACTIVE_ATTRIBUTES

    def test_reads_a_vector(self, table):
        assert table[0x0B80].shape == (4,)  # GL_ACCUM_CLEAR_VALUE

    def test_reads_a_matrix_shape(self, table):
        """A matrix is 4x4, not 16: the caller gets a 4x4 array."""
        assert table[0x0BA6].shape == (4, 4)  # GL_MODELVIEW_MATRIX

    def test_a_runtime_lookup_records_the_pname_to_query(self, table):
        """``(_L(0x86A2),)`` -- the size itself comes from a glGetIntegerv."""
        entry = table[0x86A3]  # GL_COMPRESSED_TEXTURE_FORMATS
        assert entry.lookup == 0x86A2
        assert entry.shape == ()

    def test_covers_the_whole_table(self, table):
        """Fewer entries than assignments: aliased enums share a pname."""
        assert len(table) > 1700

    def test_a_repeated_pname_takes_the_last_assignment(self, table):
        """``_m[pname] = ...`` twice is a dict overwrite, and must stay one."""
        source = open(
            os.path.join(PACKAGE, 'raw', 'GL', '_glgets.py'), encoding='utf-8'
        ).read()
        namespace = {}
        exec(compile(source, '_glgets.py', 'exec'), namespace)
        assert len(table) == len(namespace['_glget_size_mapping'])

    def test_every_api_has_a_table(self):
        for api in ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLX', 'WGL'):
            path = os.path.join(PACKAGE, 'raw', api, '_glgets.py')
            if os.path.exists(path):
                assert glgets.read_table(path) is not None


class TestCounts:
    def test_a_shape_has_a_total_element_count(self, table):
        assert table[0x0BA6].count == 16
        assert table[0x8B89].count == 1

    def test_a_runtime_lookup_has_no_static_count(self, table):
        assert table[0x86A3].count is None


class TestEmission:
    def test_entries_are_sorted_for_a_binary_search(self, table):
        text = glgets.emit_table('GL', table)
        pnames = [
            int(line.split('{')[1].split(',')[0], 0)
            for line in text.splitlines()
            if line.strip().startswith('{0x')
        ]
        assert pnames == sorted(pnames)
        assert len(pnames) == len(set(pnames))

    def test_the_table_declares_its_length(self, table):
        text = glgets.emit_table('GL', table)
        assert 'pygl_glget_GL_count' in text
