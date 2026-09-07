"""Resolving a command that several extensions declare.

``glUniform1i64NV`` is declared by ``GL_NV_gpu_shader5`` and by
``GL_AMD_gpu_shader_int64``.  A driver advertising one and not the other has
the function, so checking a single recorded extension string refuses an entry
point the context provides -- which is what this asserts it no longer does.
"""

import pytest

from OpenGL import error, extensions
from OpenGL._dispatch import support


class FakePlatform:
    """A context advertising exactly the extensions it was given."""

    def __init__(self, *advertised):
        self.advertised = set(advertised)
        self.asked = []

    def checkExtension(self, name):
        self.asked.append(name)
        return name in self.advertised


def present(platform_, extension, alternates=''):
    return support._any_extension_present(platform_, extension, alternates)


def test_the_recorded_extension_is_enough():
    assert present(FakePlatform('GL_AMD_gpu_shader_int64'), 'GL_AMD_gpu_shader_int64')


def test_an_alternate_is_enough():
    """The case the NVIDIA driver presents: the alias, not the record."""
    platform_ = FakePlatform('GL_NV_gpu_shader5')
    assert present(platform_, 'GL_AMD_gpu_shader_int64', 'GL_NV_gpu_shader5')


def test_none_of_them_means_absent():
    platform_ = FakePlatform('GL_ARB_sync')
    assert not present(platform_, 'GL_AMD_gpu_shader_int64', 'GL_NV_gpu_shader5')


def test_a_core_alternate_needs_no_string():
    """A version that adopted the command declares it unconditionally."""
    platform_ = FakePlatform()
    assert present(platform_, 'GL_ARB_ES2_compatibility', 'GL_VERSION_GL_4_1')
    assert platform_.asked == ['GL_ARB_ES2_compatibility']


def test_an_empty_alternate_list_is_not_an_extension():
    assert not present(FakePlatform(), 'GL_FOO', '')
    assert not present(FakePlatform(), 'GL_FOO', ',,')


@pytest.mark.parametrize(
    'name', ['glUniform1i64NV', 'glGetUniformui64vNV', 'glProgramUniform1i64NV']
)
def test_the_shipped_table_records_the_alias(name):
    """The generated table has to carry it for the rule to have anything to use."""
    import OpenGL.GL  # noqa: F401 -- installs the dispatch layer
    from OpenGL import _dispatch

    proc = _dispatch.entry_points.get(('GL', name))
    if proc is None:
        pytest.skip('%s is not implemented in C' % (name,))
    assert proc.extension


class TestChoosingAmongAlternates:
    """``OpenGL.extensions.alternate``: one name over several entry points.

    A program that wants ``glMultiDrawElements`` and does not care whether the
    driver spells it core or ``EXT`` writes
    ``alternate(glMultiDrawElementsEXT, glMultiDrawElements)`` and calls the
    result.  What it is entitled to is that the *first* of the alternatives
    that resolved is the one called, that ``bool()`` answers whether any of
    them did, and that calling when none did raises rather than doing nothing.
    """

    class Resolved:
        """Stands in for an entry point the driver provided."""

        def __init__(self, name):
            self.__name__ = name

        def __bool__(self):
            return True

        def __call__(self, *arguments):
            return (self.__name__,) + arguments

    class Unresolved:
        """Stands in for one it did not: falsy, and raises if called."""

        def __init__(self, name):
            self.__name__ = name

        def __bool__(self):
            return False

        def __call__(self, *arguments):  # pragma: no cover - never reached
            raise AssertionError('an unresolved entry point was called')

    def test_the_first_resolved_alternative_is_the_one_called(self):
        chosen = extensions.alternate(
            self.Unresolved('glFooEXT'),
            self.Resolved('glFooARB'),
            self.Resolved('glFoo'),
        )
        assert chosen(1, 2) == ('glFooARB', 1, 2)

    def test_it_takes_its_name_from_the_first_argument(self):
        """``alternate(fn, ...)`` names itself after ``fn``; a str names it."""
        assert extensions.alternate(self.Resolved('glFooEXT')).__name__ == 'glFooEXT'
        assert extensions.alternate(
            'glFoo', self.Resolved('glFooEXT')
        ).__name__ == 'glFoo'

    def test_a_name_given_as_a_string_is_not_one_of_the_alternatives(self):
        chosen = extensions.alternate('glFoo', self.Resolved('glFooEXT'))
        assert chosen() == ('glFooEXT',)

    def test_bool_is_whether_any_of_them_resolved(self):
        assert extensions.alternate(
            self.Unresolved('glFooEXT'), self.Resolved('glFoo')
        )
        assert not extensions.alternate(
            self.Unresolved('glFooEXT'), self.Unresolved('glFoo')
        )

    def test_calling_with_none_resolved_raises_naming_all_of_them(self):
        chosen = extensions.alternate(
            self.Unresolved('glFooEXT'), self.Unresolved('glFooARB')
        )
        with pytest.raises(error.NullFunctionError) as caught:
            chosen()
        assert 'glFooEXT' in str(caught.value)
        assert 'glFooARB' in str(caught.value)

    def test_the_choice_is_made_once_and_kept(self):
        """``LateBind`` replaces itself with the winner on the first call.

        Which is the point of it: the alternatives are asked once, not on
        every call in a draw loop.  Detected by making an *earlier*
        alternative resolve after the first call -- a second lookup would
        prefer it, a bound implementation never sees it.
        """

        class ResolvesLater(TestChoosingAmongAlternates.Resolved):
            resolved = False

            def __bool__(self):
                return self.resolved

        first = ResolvesLater('glFooEXT')
        chosen = extensions.alternate(first, self.Resolved('glFoo'))

        assert chosen() == ('glFoo',)
        first.resolved = True
        assert chosen() == ('glFoo',), (
            'the second call went back to the alternatives instead of the '
            'implementation the first one bound'
        )

    def test_the_real_entry_points_resolve_through_it(self):
        """The case the suite is really about: a live pair from OpenGL.GL."""
        from OpenGL.GL import glMultiDrawElements
        from OpenGL.GL.EXT.multi_draw_arrays import glMultiDrawElementsEXT

        chosen = extensions.alternate(glMultiDrawElementsEXT, glMultiDrawElements)
        assert bool(chosen) == (
            bool(glMultiDrawElementsEXT) or bool(glMultiDrawElements)
        )
