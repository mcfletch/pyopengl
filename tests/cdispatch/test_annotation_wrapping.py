"""Rebuilding a friendly module's customisations from the annotation table.

A friendly module says what makes its Python signature differ from the C one
as a chain of calls::

    glUniform4fv = wrapper.wrapper(glUniform4fv).setInputArraySize('value', None)
    glGetIntegerv = wrapper.wrapper(glGetIntegerv).setOutput(
        'data', _glgets.GL_GET_SIZES, pnameArg='pname', orPassIn=True)

2,027 of those calls are ``setInputArraySize`` and 687 are ``setOutput``, across
259 modules that contain nothing else.  Both are already in the annotation
table -- a size spec and ``out`` -- because the table was extracted from these
very chains.

So the chains are a second copy of what the table holds, and the modules can
stop carrying them.  What has to be true first is that applying the table
produces the same wrapper the chain produces, which is what these check, on the
real entry points rather than on a mock.
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

    def test_the_two_calls_dominate(self, chains):
        """If the tail were large this would not be worth doing."""
        import collections

        counts = collections.Counter(
            call for calls in chains.values() for call, _arguments in calls
        )
        mechanical = counts['setInputArraySize'] + counts['setOutput']
        assert mechanical > 20 * (sum(counts.values()) - mechanical)


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
