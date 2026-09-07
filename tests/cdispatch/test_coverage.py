"""Registry coverage, asserted rather than claimed.

Complete coverage of the Khronos registry is a property that lapses quietly:
an entry point Khronos adds is simply absent until somebody notices.  These
cases make it a red test instead, and they are what the scheduled regeneration
job runs to decide whether a registry update needs a human.
"""

import os

import pytest

from cdispatch import emit_c, extract, upstream

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY),
    reason='the Khronos registry is not checked out at src/khronosapi',
)


@pytest.fixture(scope='module')
def report():
    return upstream.compare(PACKAGE, REGISTRY)


class TestRegistryCoverage:
    """No *new* drift against the registry.

    The shipped tree already lags the registry by a handful of commands and a
    hundred-odd enums, all recorded in registry_baseline.json with the reason.
    What must not happen unnoticed is a registry pull adding more.
    """

    @pytest.fixture(scope='class')
    @staticmethod
    def drift(report):
        return upstream.new_drift(report)

    def test_no_new_registry_command_lacks_a_binding(self, drift):
        assert drift['missing_commands'] == [], drift['missing_commands'][:40]

    def test_no_binding_has_the_wrong_arity(self, drift):
        """Arity is never allowed to differ, baseline or not.

        Argument *types* legitimately differ -- an array parameter is declared
        as an ArrayDatatype rather than a raw pointer -- but a binding that
        takes a different number of arguments than the registry declares
        cannot be called correctly.
        """
        assert drift['arity_mismatches'] == [], drift['arity_mismatches'][:40]

    def test_no_new_argument_name_differences(self, drift):
        assert drift['argument_name_differences'] == []

    def test_no_new_enums_are_missing(self, drift):
        assert drift['missing_enums'] == [], drift['missing_enums'][:40]

    def test_the_baseline_explains_itself(self):
        """Every recorded difference says why it is there."""
        baseline = upstream.load_baseline()
        for key in (
            'missing_commands',
            'argument_name_differences',
            'missing_enums',
        ):
            assert baseline[key]['_reason'].strip()


class TestEmissionCoverage:
    """What the C implements, held at or above where it stands.

    The number is asserted rather than described so that a change which
    silently drops entry points back to ctypes shows up as a failure.
    """

    #: Raise this as families land; never lower it without saying why.
    MINIMUM = 4560

    def test_enough_bindings_are_emitted(self):
        commands = extract.extract_tree(PACKAGE)
        emitted = [c for c in commands.values() if emit_c.is_emittable(c)]
        assert len(emitted) >= self.MINIMUM, (
            'emission fell to %d from %d' % (len(emitted), self.MINIMUM)
        )

    def test_the_retaining_family_is_emitted(self):
        """A retained argument outlives the call, so the C has to keep it.

        Forgetting is a crash rather than a leak, which is why the family is
        derived from setStoreValues rather than guessed at.
        """
        commands = extract.extract_tree(PACKAGE)
        retaining = [
            key
            for key, command in commands.items()
            if any(parameter.retain for parameter in command.parameters)
        ]
        assert retaining, 'the annotation stopped being derived at all'
        for key in retaining:
            assert emit_c.is_emittable(commands[key]), key

    def test_every_retained_parameter_is_honoured_or_excluded_for_a_reason(self):
        """Nothing carries the annotation without either the code that honours
        it or a stated reason for staying on the ctypes path."""
        commands = extract.extract_tree(PACKAGE)
        unexplained = [
            '%s.%s' % key
            for key, command in commands.items()
            if any(parameter.retain for parameter in command.parameters)
            and not emit_c.is_emittable(command)
            and not emit_c.exclusion_reason(command)
        ]
        assert unexplained == [], unexplained[:20]

    def test_every_command_not_emitted_has_a_stated_reason(self):
        """Nothing is left on ctypes by accident."""
        commands = extract.extract_tree(PACKAGE)
        unexplained = [
            '%s.%s' % key
            for key, command in commands.items()
            if not emit_c.is_emittable(command)
            and not emit_c.exclusion_reason(command)
        ]
        assert unexplained == [], unexplained[:40]
