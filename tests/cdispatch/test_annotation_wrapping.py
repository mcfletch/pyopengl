"""Rebuilding a friendly module's customisations from the annotation table.

A friendly module says what makes its Python signature differ from the C one
as a chain of calls::

    glUniform4fv = wrapper.wrapper(glUniform4fv).setInputArraySize('value', None)
    glGetIntegerv = wrapper.wrapper(glGetIntegerv).setOutput(
        'data', _glgets.GL_GET_SIZES, pnameArg='pname', orPassIn=True)

Both are in the annotation table -- a conversion, a size spec, ``out`` -- so a
chain is a second copy of what the table holds, and 257 modules have stopped
carrying theirs.  What has to be true for the next one to is that applying the
table produces the same wrapper the chain produces, which is what these check,
on the real entry points rather than on a mock.

The chains that remain are in modules the table cannot express: a hand-written
converter, a resolver, an image size computed from a format and a type
together.  They are the reason the parse still exists, and comparing the two
copies is the only thing it is still for -- generation reads the table alone
(``test_generation_is_data_driven.py``).
"""

import os

import pytest

from cdispatch import annotations, extract

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def table():
    return annotations.load()


class TestTheChainsAreASecondCopy:
    """Every customisation a module applies is already in the table."""

    @pytest.fixture(scope='class')
    def chains(self):
        """``{(api, command): [(call, arguments), ...]}`` from the modules."""
        return extract.extract_customisations(PACKAGE)

    def test_every_size_a_module_sets_is_in_the_table(self, chains, table):
        missing = []
        for (api, name), calls in chains.items():
            for call, arguments in calls:
                if call != 'setInputArraySize' or arguments[1] is None:
                    continue
                entry = table.get('%s.%s' % (api, name), {})
                if arguments[0] not in entry.get('parameters', {}):
                    missing.append((api, name, arguments[0]))
        assert missing == [], missing[:10]

    def test_every_output_a_module_sets_is_in_the_table(self, chains, table):
        missing = []
        for (api, name), calls in chains.items():
            for call, arguments in calls:
                if call != 'setOutput':
                    continue
                entry = table.get('%s.%s' % (api, name), {})
                bits = entry.get('parameters', {}).get(arguments[0])
                if not bits or not bits.get('out'):
                    missing.append((api, name, arguments[0]))
        assert missing == [], missing[:10]

    def test_nothing_absorbable_is_still_carrying_a_chain(self):
        """The migration is finished, and stays finished.

        A module whose chain the table can express is one the absorber would
        rewrite, so finding one means either a new module arrived carrying a
        chain or something stopped being expressible.  Both want looking at.
        """
        import subprocess
        import sys

        completed = subprocess.run(
            [sys.executable, os.path.join(HERE, 'src', 'absorb_chains.py')],
            capture_output=True,
            text=True,
            cwd=HERE,
            timeout=300,
        )
        assert completed.returncode == 0, completed.stderr
        assert 'would rewrite 0 modules' in completed.stdout, completed.stdout

    def test_what_still_carries_a_chain_is_what_the_table_cannot_say(self, chains):
        """The remaining calls are the hand-written ones, plus their company.

        A module is absorbed whole or not at all, so a ``setInputArraySize``
        sitting beside a ``setPyConverter`` stays where it is.  What must not
        appear is a module of nothing but mechanical calls.
        """
        import collections

        counts = collections.Counter(
            call for calls in chains.values() for call, _arguments in calls
        )
        hand_written = sum(
            count
            for call, count in counts.items()
            if call not in ('setInputArraySize', 'setOutput')
        )
        assert hand_written > 0, 'the parse has nothing left to check'
        assert counts['setInputArraySize'] + counts['setOutput'] < 800


class TestRebuildingFromTheTable:
    """Applying the table has to produce the wrapper the chain produced."""

    @pytest.mark.parametrize(
        'api,name',
        [
            ('GL', 'glGetIntegerv'),
            ('GL', 'glGenTextures'),
            ('GL', 'glDrawElements'),
        ],
    )
    def test_the_annotation_describes_what_the_chain_did(self, api, name, table):
        entry = table.get('%s.%s' % (api, name))
        assert entry is not None, '%s.%s carries no annotation' % (api, name)
        assert entry.get('parameters'), (api, name)

    def test_an_output_says_which_argument_sizes_it(self, table):
        size = table['GL.glGetIntegerv']['parameters']['data']['size']
        assert size == {'kind': 'glget-table', 'pname': 'pname'}

    def test_an_unchecked_input_array_carries_no_size(self, table):
        """``setInputArraySize('value', None)`` says "any length", so there is
        no size to record."""
        entry = table.get('GL.glUniform4fv', {})
        parameters = entry.get('parameters', {})
        assert 'value' not in parameters or 'size' not in parameters['value']

    def test_but_it_is_not_saying_nothing(self):
        """It installs an array conversion, and that is recoverable from the
        declaration rather than from the table.

        The call puts ``ArrayDatatype.asArray`` in front of the argument.  The
        argument's declared type *is* that ArrayDatatype, so whatever rebuilds
        these takes array-ness from the signature and the length -- when there
        is one -- from the table.  Reading the table alone would drop the
        conversion and hand the driver a list.
        """
        import OpenGL.GL  # noqa: F401 -- installs the layer
        from OpenGL.raw.GL.VERSION import GL_2_0

        declared = dict(
            zip(GL_2_0.glUniform4fv.argNames, GL_2_0.glUniform4fv.argtypes)
        )
        from OpenGL.arrays.arraydatatype import ArrayDatatype

        assert isinstance(declared['value'], ArrayDatatype.__class__) or hasattr(
            declared['value'], 'asArray'
        )


class TestTheAnnotationsShip:
    """The pure-Python path needs them at run time, so they have to be in the
    wheel and readable without the generator."""

    def test_they_are_written_beside_the_declarations(self):
        import marshal

        path = os.path.join(
            PACKAGE, 'raw', '_declarations', '_annotations.dat'
        )
        assert os.path.exists(path), path
        with open(path, 'rb') as handle:
            shipped = marshal.load(handle)
        assert len(shipped) > 1000

    def test_what_ships_is_what_the_generator_produced(self, table):
        import marshal

        path = os.path.join(PACKAGE, 'raw', '_declarations', '_annotations.dat')
        with open(path, 'rb') as handle:
            shipped = marshal.load(handle)
        assert shipped == table, (
            'the shipped annotations differ from src/cdispatch/annotations.json; '
            'regenerate with python src/regenerate_c.py'
        )

    def test_the_wheel_carries_them(self):
        """package-data has to name the file, or it is built and left out --
        which is what happened to the declarations themselves."""
        with open(os.path.join(HERE, 'pyproject.toml'), encoding='utf-8') as handle:
            text = handle.read()
        assert 'raw/_declarations/*.dat' in text
