"""The plug-in registry, and the module list a freezer builds from it."""

from OpenGL import plugins


def test_registered_modules_drops_the_attribute():
    """An import path names an attribute; a freezer wants the module."""
    modules = plugins.registered_modules()
    assert 'OpenGL.platform.win32' in modules
    assert 'OpenGL.platform.win32.Win32Platform' not in modules


def test_registered_modules_covers_every_registry():
    """Platform plug-ins and format handlers are separate registries."""
    modules = plugins.registered_modules()
    assert 'OpenGL.platform.linux' in modules
    assert 'OpenGL.arrays.numpymodule' in modules
    assert 'OpenGL.arrays.vbo' in modules


def test_registered_modules_is_sorted_and_unique():
    modules = plugins.registered_modules()
    assert modules == sorted(set(modules))


def test_registered_modules_reads_the_registry_rather_than_a_list():
    """A plug-in registered by a third party is reported like any other."""

    class Sample(plugins.Plugin):
        registry = []

    Sample('sample', 'sample_package.sample_module.SampleEntry')
    try:
        assert 'sample_package.sample_module' in plugins.registered_modules()
    finally:
        Sample.registry.clear()


def test_registered_modules_prefix_selects_one_package():
    """The prefix matches whole dotted components, not bare characters."""

    class Sample(plugins.Plugin):
        registry = []

    Sample('near-miss', 'OpenGLContextish.module.Entry')
    try:
        modules = plugins.registered_modules('OpenGL')
        assert 'OpenGLContextish.module' not in modules
        assert 'OpenGL.platform.linux' in modules
        assert all(name == 'OpenGL' or name.startswith('OpenGL.') for name in modules)
    finally:
        Sample.registry.clear()
