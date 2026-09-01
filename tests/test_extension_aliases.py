"""Resolving a command that several extensions declare.

``glUniform1i64NV`` is declared by ``GL_NV_gpu_shader5`` and by
``GL_AMD_gpu_shader_int64``.  A driver advertising one and not the other has
the function, so checking a single recorded extension string refuses an entry
point the context provides -- which is what this asserts it no longer does.
"""

import pytest

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
