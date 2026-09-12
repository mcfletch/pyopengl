#! /usr/bin/env python3
"""The three copies of the glGet output sizes say the same thing.

``glGetFloatv(pname)`` allocates its output array from a recorded size and
hands the driver a pointer.  Where the record is shorter than what the driver
writes, the driver writes past the end of a live allocation: nothing raises,
the bytes belong to some other object, and the program continues with that
object quietly damaged.  On Windows the NT heap notices at the next free and
the process dies with ``STATUS_HEAP_CORRUPTION`` somewhere unrelated -- in one
case inside ``glfw.destroy_window``, one test later, in a run whose tests had
all passed.

``tests/gl/test_glget_sizes.py`` walks the shipped table against the driver in
front of it, which is the half of this a running GL can answer.  What it cannot
answer is a pname no driver in CI implements, and it cannot answer the *other*
half at all: the sizes live in three files, all generated from one source, and
all three have to be regenerated together.

    src/glgetsizes.csv                        hand-maintained, the source
    OpenGL/raw/<API>/_glgets.py               python src/regen_glgets.py
    accelerate/src/c/generated/pygl_glgets.h  python src/regenerate_c.py

The ctypes path reads the Python; the C dispatch path compiles the header.
Correcting the CSV and regenerating only the Python leaves the C path still
overrunning, which is what it did until the extension was rebuilt -- so the
two shipped tables agreeing is a thing to check rather than a thing to
remember.

See plans/GLGET-SIZES.md.
"""

import os
import re

import paths
import pytest

CSV = os.path.join(paths.SRC, 'glgetsizes.csv')
HEADER = os.path.join(
    paths.ROOT, 'accelerate', 'src', 'c', 'generated', 'pygl_glgets.h'
)

#: ``_m[0x0D5B] = (1,) # GL_ACCUM_ALPHA_BITS`` in a generated ``_glgets.py``.
#: A few values are written in decimal, and one carries a ``#TODO`` note
#: between the size and the enum name, so the size is everything up to the
#: last ``#``.
PYTHON_ROW = re.compile(
    r'^_m\[(0x[0-9A-Fa-f]+|\d+)\]\s*=\s*(.*)#\s*([A-Za-z0-9_]+)\s*$'
)

#: ``static const PyGLGetSize pygl_glget_GL[] = {`` and its rows.
C_TABLE = re.compile(r'^static const PyGLGetSize pygl_glget_([A-Za-z0-9_]+)\[\]')
C_ROW = re.compile(
    r'^\s*\{(0x[0-9A-Fa-f]+),\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\}'
)


def python_tables():
    """``{api: {pname: size text}}`` from the shipped ``_glgets.py`` files."""
    found = {}
    raw = os.path.join(paths.PACKAGE, 'raw')
    for api in sorted(os.listdir(raw)):
        path = os.path.join(raw, api, '_glgets.py')
        if not os.path.exists(path):
            continue
        rows = {}
        with open(path, encoding='utf-8') as handle:
            for line in handle:
                match = PYTHON_ROW.match(line.strip())
                if match:
                    value, size, _name = match.groups()
                    rows[_number(value)] = size.split("#", 1)[0].strip()
        found[api] = rows
    return found


def c_tables():
    """``{api: {pname: (dim0, dim1, lookup)}}`` from the generated header."""
    if not os.path.exists(HEADER):
        return {}
    found, api = {}, None
    with open(HEADER, encoding='utf-8') as handle:
        for line in handle:
            heading = C_TABLE.match(line)
            if heading:
                api = heading.group(1)
                found[api] = {}
                continue
            if api is None:
                continue
            row = C_ROW.match(line)
            if row:
                pname, dim0, dim1, lookup = row.groups()
                found[api][int(pname, 16)] = (
                    int(dim0), int(dim1), int(lookup, 16)
                )
            elif line.startswith('}'):
                api = None
    return found


def _number(text):
    """``0x0D5B`` or ``103050`` -- both spellings are in the tables."""
    text = text.strip()
    return int(text, 16) if text.lower().startswith('0x') else int(text)


def _as_c(size):
    """The Python size text as the header records it, or None if it cannot be.

    Four shapes, which are all the tables use:

    ``(1,)``            one dimension of that many
    ``(4, 4)``          two, which is how a matrix pname is recorded
    ``(_L(0x0CB0),)``   the count is read from another query at call time,
                        so the header carries no dimension and the pname to
                        ask instead
    ``(2, _L(0x8E11),)`` that many of whatever the other query answers --
                        GL_MULTISAMPLE_COVERAGE_MODES_NV is pairs
    """
    size = size.strip()
    lookup = re.match(r'^\(\s*_L\(\s*(0x[0-9A-Fa-f]+|\d+)\s*\)\s*,?\s*\)$', size)
    if lookup:
        return (0, 0, _number(lookup.group(1)))
    counted = re.match(
        r'^\(\s*(\d+)\s*,\s*_L\(\s*(0x[0-9A-Fa-f]+|\d+)\s*\)\s*,?\s*\)$', size
    )
    if counted:
        return (int(counted.group(1)), 0, _number(counted.group(2)))
    one = re.match(r'^\(\s*(\d+)\s*,\s*\)$', size)
    if one:
        return (int(one.group(1)), 0, 0)
    pair = re.match(r'^\(\s*(\d+)\s*,\s*(\d+)\s*,?\s*\)$', size)
    if pair:
        return (int(pair.group(1)), int(pair.group(2)), 0)
    return None


PYTHON = python_tables()
C = c_tables()


class TestTheTablesAreThere:
    """A comparison over an empty table compares nothing."""

    def test_the_python_tables_are_read(self):
        assert PYTHON, 'no OpenGL/raw/<API>/_glgets.py was read'
        assert sum(len(rows) for rows in PYTHON.values()) > 1000, {
            api: len(rows) for api, rows in PYTHON.items()
        }

    def test_the_c_table_is_read_where_it_is_generated(self):
        if not os.path.exists(HEADER):
            pytest.skip(
                'accelerate/src/c/generated/pygl_glgets.h is written by '
                '`python src/regenerate_c.py` and this checkout has not been '
                'generated into'
            )
        assert C, 'the header is there and no table was read out of it'


class TestTheCopiesAgree:
    """The ctypes path reads the Python and the C path compiles the header."""

    @pytest.mark.parametrize('api', sorted(C))
    def test_every_pname_in_the_c_table_is_in_the_python_one(self, api):
        rows = PYTHON.get(api)
        assert rows is not None, (
            'the header carries a %s table and there is no '
            'OpenGL/raw/%s/_glgets.py to have generated it' % (api, api)
        )
        missing = sorted(set(C[api]) - set(rows))
        assert not missing, (
            'the %s table compiled into the extension has %d pname(s) the '
            'shipped Python table does not, so the two paths size the same '
            'query differently: %s'
            % (api, len(missing), ['0x%04X' % one for one in missing[:20]])
        )

    @pytest.mark.parametrize('api', sorted(C))
    def test_every_recorded_size_is_the_same_size(self, api):
        rows = PYTHON.get(api) or {}
        disagreements = []
        unreadable = []
        compared = 0
        for pname, recorded in sorted(C[api].items()):
            size = rows.get(pname)
            if size is None:
                continue                    # the case above reports it
            expected = _as_c(size)
            if expected is None:
                unreadable.append('0x%04X: %s' % (pname, size))
                continue
            compared += 1
            if expected != recorded:
                disagreements.append(
                    '0x%04X: the Python says %s and the header says %s'
                    % (pname, size, recorded)
                )
        assert not unreadable, (
            'these %s sizes are written in a shape this comparison cannot '
            'read, so it would pass over them without comparing anything.  '
            'Teach `_as_c` the shape, or write the size the way its '
            'neighbours are written:\n  %s' % (api, '\n  '.join(unreadable))
        )
        assert not disagreements, (
            'the %s output sizes disagree between the two shipped tables.  A '
            'program on the ctypes path and one on the C path then allocate '
            'differently for the same query, and the shorter of the two is a '
            'heap overrun in every program making it.  All three copies are '
            'generated from src/glgetsizes.csv and all three have to be '
            'regenerated:\n  %s' % (api, '\n  '.join(disagreements))
        )
        assert compared > 500, (
            'only %d %s size(s) were compared, so this passed having checked '
            'almost nothing' % (compared, api)
        )


class TestTheSourceCoversWhatIsShipped:
    """``src/glgetsizes.csv`` is the one hand-maintained copy."""

    def test_every_python_pname_comes_from_a_named_enum(self):
        """A row whose comment names no enum is one nobody can regenerate."""
        nameless = []
        raw = os.path.join(paths.PACKAGE, 'raw')
        for api in sorted(PYTHON):
            path = os.path.join(raw, api, '_glgets.py')
            with open(path, encoding='utf-8') as handle:
                for number, line in enumerate(handle, 1):
                    stripped = line.strip()
                    if stripped.startswith('_m[') and not PYTHON_ROW.match(stripped):
                        nameless.append('%s/_glgets.py:%d: %s' % (api, number, stripped))
        assert not nameless, (
            'these rows are not written the way `src/regen_glgets.py` writes '
            'one -- value, size, and the enum name in a comment -- so a '
            'regeneration would not produce them and they would be lost:\n'
            '  %s' % '\n  '.join(nameless)
        )

    def test_the_csv_names_every_size_the_gl_table_ships(self):
        if not os.path.exists(CSV):
            pytest.skip('src/glgetsizes.csv is not in this checkout')
        named = set()
        with open(CSV, encoding='utf-8') as handle:
            for line in handle:
                parts = line.split('\t')
                if parts and parts[0].strip():
                    named.add(parts[0].strip())
        shipped = set()
        path = os.path.join(paths.PACKAGE, 'raw', 'GL', '_glgets.py')
        with open(path, encoding='utf-8') as handle:
            for line in handle:
                match = PYTHON_ROW.match(line.strip())
                if match:
                    shipped.add(match.group(3))
        missing = sorted(shipped - named)
        assert not missing, (
            '%d size(s) ship in OpenGL/raw/GL/_glgets.py and are not in '
            'src/glgetsizes.csv, which is the copy a person edits -- so the '
            'next `python src/regen_glgets.py` drops them and every query '
            'below falls back to a single value: %s'
            % (len(missing), missing[:20])
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
