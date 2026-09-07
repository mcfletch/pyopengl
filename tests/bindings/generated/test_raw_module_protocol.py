"""What a tool asking about ``OpenGL.raw`` gets back.

The modules there are built from the shipped declaration tables rather than
imported from files, and a synthesised module that answers nothing about itself
is worse than a missing one: walking ``OpenGL.raw.GL.ARB`` to find out which
extensions PyOpenGL knows about is a real thing to do, and an empty list is an
answer that reads as "none" rather than as "ask somebody else".

So the names are enumerable, and each module says where its definitions came
from.
"""

import pkgutil

import pytest

# Importing one is what installs the finder: PyOpenGL defers that until a
# generated name is first asked for, so asking has to come before the question
# of whether it is installed.  A package will not do -- those are real files,
# and the finder is never consulted about them.
import OpenGL.raw.GL.ARB
import OpenGL.raw.GL.VERSION.GL_1_1  # noqa: F401 - installs the finder
from OpenGL._dispatch import finder

pytestmark = pytest.mark.skipif(
    finder.installed() is None,
    reason='the generated modules are being imported from files',
)


@pytest.fixture(scope='module')
def arb():
    return OpenGL.raw.GL.ARB


class TestEnumeration:
    def test_a_raw_package_lists_the_modules_it_holds(self, arb):
        found = [name for _importer, name, _ispkg in pkgutil.iter_modules(arb.__path__)]
        assert 'vertex_buffer_object' in found
        assert 'texture_storage' in found

    def test_the_count_is_the_whole_extension_set(self, arb):
        """An empty list is the failure this guards; so is a handful."""
        found = list(pkgutil.iter_modules(arb.__path__))
        assert len(found) > 100

    def test_walking_the_tree_reaches_the_generated_modules(self):
        import OpenGL.raw.GL

        walked = {
            name
            for _importer, name, _ispkg in pkgutil.walk_packages(
                OpenGL.raw.GL.__path__, 'OpenGL.raw.GL.'
            )
        }
        assert 'OpenGL.raw.GL.VERSION.GL_1_1' in walked
        assert 'OpenGL.raw.GL.ARB.vertex_buffer_object' in walked

    def test_the_real_files_are_still_listed(self, arb):
        """_types and friends are files, and must not be lost to the synthesis."""
        import OpenGL.raw.GL

        found = [
            name for _importer, name, _ispkg in pkgutil.iter_modules(OpenGL.raw.GL.__path__)
        ]
        assert '_types' in found

    def test_packages_are_reported_as_packages(self):
        import OpenGL.raw.GL

        kinds = {
            name: ispkg
            for _importer, name, ispkg in pkgutil.iter_modules(OpenGL.raw.GL.__path__)
        }
        assert kinds['ARB'] is True
        assert kinds['_types'] is False


class TestWhereADefinitionCameFrom:
    def test_a_generated_module_names_its_table(self):
        from OpenGL.raw.GL.VERSION import GL_1_1

        assert GL_1_1.__file__.endswith('GL.dat')

    def test_the_spec_origin_is_the_same_file(self):
        from OpenGL.raw.GL.VERSION import GL_1_1

        assert GL_1_1.__spec__.origin == GL_1_1.__file__

    def test_the_table_it_names_is_the_one_that_holds_it(self):
        from OpenGL.raw.GLES2.VERSION import GLES2_2_0

        assert GLES2_2_0.__file__.endswith('GLES2.dat')

    def test_the_named_file_is_readable(self):
        """A __file__ nothing can open is worse than none at all."""
        from OpenGL.raw.GL.VERSION import GL_1_1

        with open(GL_1_1.__file__, 'rb') as handle:
            assert handle.read(1)
