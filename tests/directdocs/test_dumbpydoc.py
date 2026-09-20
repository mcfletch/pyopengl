"""Which page declares a name, and what the other pages say instead.

Almost every name in PyOpenGL is reachable from several modules -- the
declaration table's own, the friendly module beside it, and the package that
re-exports both.  Declaring it on each puts the same entry in the index several
times and makes a cross-reference to it ambiguous, so one module is chosen and
the rest link.  These hold that choice, and the way two exports of one command
are recognised as the same thing despite being two objects.
"""

import pytest

from directdocs import dumbpydoc


class Fake:
    """Stands in for something a module exports.

    Enough of a :class:`directdocs.model.PyFunction` to be rendered: a name, a
    parameter list and no docstring.
    """

    docstring = None
    parameters = ()

    def __init__(self, module=None, name='thing'):
        self.name = name
        if module is not None:
            self.__module__ = module


class FakeModule(dumbpydoc.PyModule):
    """A module whose contents are given rather than imported."""

    def __init__(self, name, functions=(), constants=(), classes=()):
        super().__init__(name)
        self.functions = list(functions)
        self.constants = list(constants)
        self.classes = list(classes)
        self._inspected = True


class TestIdentity:
    def test_two_exports_of_one_command_are_one_thing(self):
        """The friendly module builds its own entry point per command, so the
        two objects are not identical and must still be recognised."""
        raw = Fake('OpenGL.raw.GL.VERSION.GL_1_0')
        friendly = Fake('OpenGL.raw.GL.VERSION.GL_1_0')
        assert raw is not friendly
        assert dumbpydoc.identity(
            raw, FakeModule('OpenGL.raw.GL.VERSION.GL_1_0'), 'glBegin'
        ) == dumbpydoc.identity(
            friendly, FakeModule('OpenGL.GL'), 'glBegin'
        )

    def test_the_same_name_from_two_places_stays_apart(self):
        a = Fake('OpenGL.arrays.vbo')
        b = Fake('OpenGL.GL.shaders')
        assert dumbpydoc.identity(
            a, FakeModule('OpenGL.arrays.vbo'), 'Implementation'
        ) != dumbpydoc.identity(
            b, FakeModule('OpenGL.GL.shaders'), 'Implementation'
        )

    def test_something_that_says_nothing_belongs_where_it_was_found(self):
        """An instance has no ``__module__`` of its own; where it was found is
        then the only answer there is."""
        value = 17
        assert getattr(value, '__module__', None) is None
        assert dumbpydoc.identity(value, FakeModule('OpenGL.GL'), 'x') == (
            ('OpenGL.GL', 'x')
        )


class TestOwnership:
    def test_the_friendly_module_declares_rather_than_the_raw_one(self):
        """`OpenGL.GL.VERSION.GL_1_0` is what a reader imports from; the raw
        module beside it is the table it was built from."""
        target = Fake('OpenGL.raw.GL.VERSION.GL_1_0')
        raw = FakeModule(
            'OpenGL.raw.GL.VERSION.GL_1_0', functions=[('glBegin', target)]
        )
        friendly = FakeModule(
            'OpenGL.GL.VERSION.GL_1_0', functions=[('glBegin', target)]
        )
        claims = dumbpydoc.claim_owners([raw, friendly])
        assert claims[('OpenGL.raw.GL.VERSION.GL_1_0', 'glBegin')] == (
            ('OpenGL.GL.VERSION.GL_1_0', 'glBegin')
        )

    def test_a_module_that_only_re_exports_does_not_declare(self):
        target = Fake('OpenGL.raw.GL.VERSION.GL_1_0')
        declaring = FakeModule(
            'OpenGL.GL.VERSION.GL_1_0', functions=[('glBegin', target)]
        )
        reexporting = FakeModule('OpenGL.GL', functions=[('glBegin', target)])
        claims = dumbpydoc.claim_owners([reexporting, declaring])
        owner = claims[('OpenGL.raw.GL.VERSION.GL_1_0', 'glBegin')]
        assert owner[0] == 'OpenGL.GL.VERSION.GL_1_0'

    def test_with_no_declaring_module_the_shallowest_wins(self):
        """Nothing claims to define it, so the module a reader is likeliest to
        import from takes it."""
        target = Fake('somewhere.else')
        deep = FakeModule('OpenGL.GL.ARB.imaging', constants=[('X', target)])
        shallow = FakeModule('OpenGL.GL', constants=[('X', target)])
        claims = dumbpydoc.claim_owners([deep, shallow])
        assert claims[('somewhere.else', 'X')][0] == 'OpenGL.GL'

    def test_the_declaring_module_reports_no_other_owner(self):
        target = Fake('OpenGL.GL.VERSION.GL_1_0')
        declaring = FakeModule(
            'OpenGL.GL.VERSION.GL_1_0', functions=[('glBegin', target)]
        )
        other = FakeModule('OpenGL.GL', functions=[('glBegin', target)])
        renderer = dumbpydoc.Renderer({}, dumbpydoc.claim_owners([declaring, other]))
        assert renderer.owner(declaring, 'glBegin', target) is None
        assert renderer.owner(other, 'glBegin', target) is not None


class TestReferenceLinks:
    MANIFEST = {
        'OpenGL.GL': {'glBegin': 'gl/glBegin', 'glColor3f': 'gl/glColor',
                      'glBindTexture': 'gl/glBindTexture'},
        'OpenGL.GLES3': {'glBindTexture': 'gles3/glBindTexture'},
    }

    def test_an_entry_point_with_a_reference_page_links_to_it(self):
        renderer = dumbpydoc.Renderer(self.MANIFEST, {})
        assert renderer.reference_link(FakeModule('OpenGL.GL'), 'glBegin') == (
            ':doc:`glBegin </reference/gl/glBegin>`'
        )

    def test_an_alias_links_to_the_page_that_documents_it(self):
        """`glColor3f` is documented on `glColor`."""
        renderer = dumbpydoc.Renderer(self.MANIFEST, {})
        assert renderer.reference_link(FakeModule('OpenGL.GL'), 'glColor3f') == (
            ':doc:`glColor3f </reference/gl/glColor>`'
        )

    def test_the_link_follows_the_api_the_module_belongs_to(self):
        """One entry point, two APIs, two pages: a GLES module links to the
        GLES page and a desktop module to the desktop one."""
        renderer = dumbpydoc.Renderer(self.MANIFEST, {})
        desktop = renderer.reference_link(
            FakeModule('OpenGL.GL.VERSION.GL_1_1'), 'glBindTexture'
        )
        embedded = renderer.reference_link(
            FakeModule('OpenGL.GLES3.VERSION.GLES3_3_0'), 'glBindTexture'
        )
        assert 'reference/gl/glBindTexture' in desktop
        assert 'reference/gles3/glBindTexture' in embedded

    def test_a_name_with_no_page_has_no_link(self):
        renderer = dumbpydoc.Renderer(self.MANIFEST, {})
        assert renderer.reference_link(
            FakeModule('OpenGL.GL'), 'glGenBuffersARB'
        ) is None

    @pytest.mark.parametrize(
        'module,package',
        [
            ('OpenGL.GL', 'OpenGL.GL'),
            ('OpenGL.GL.ARB.vertex_buffer_object', 'OpenGL.GL'),
            ('OpenGL.GLES3.VERSION.GLES3_3_0', 'OpenGL.GLES3'),
            ('OpenGL', 'OpenGL'),
        ],
    )
    def test_the_api_package_is_the_first_two_components(self, module, package):
        assert dumbpydoc.api_package(module) == package


class TestRendering:
    def test_a_module_declares_itself(self):
        renderer = dumbpydoc.Renderer({}, {})
        page = renderer.render(FakeModule('OpenGL.arrays.vbo'))
        assert '.. py:module:: OpenGL.arrays.vbo' in page
        assert 'OpenGL.arrays.vbo\n=================' in page

    def test_a_constant_is_declared_with_its_value(self):
        from OpenGL.constant import Constant

        constant = Constant('GL_TRIANGLES', 4)
        module = FakeModule('OpenGL.GL', constants=[('GL_TRIANGLES', constant)])
        renderer = dumbpydoc.Renderer({}, dumbpydoc.claim_owners([module]))
        page = renderer.render(module)
        assert '.. py:data:: GL_TRIANGLES' in page
        assert ':value: 0x4' in page

    def test_submodules_are_listed_but_not_put_in_the_sidebar(self):
        """A visible toctree here would put every module of the package into
        the sidebar of every page in the set."""
        module = FakeModule('OpenGL.GL')
        module.modules = ['OpenGL.GL.ARB', 'OpenGL.GL.EXT']
        page = dumbpydoc.Renderer({}, {}).render(module)
        assert ':hidden:' in page
        assert '- :doc:`OpenGL.GL.ARB <OpenGL.GL.ARB>`' in page


class TestValues:
    @pytest.mark.parametrize(
        'value,rendered',
        [(4, '0x4'), (0x8892, '0x8892'), (0, '0x0'), (-1, '-1')],
    )
    def test_an_integer_constant_reads_as_the_header_writes_it(
        self, value, rendered
    ):
        from OpenGL.constant import Constant

        assert dumbpydoc.constant_value(Constant('X', value)) == rendered

    def test_object_is_spelled_without_its_module(self):
        class Base:
            name = 'builtins.object'

        assert dumbpydoc.base_name(Base()) == 'object'

    def test_any_other_base_keeps_its_module(self):
        class Base:
            name = 'OpenGL.arrays.vbo.VBO'

        assert dumbpydoc.base_name(Base()) == 'OpenGL.arrays.vbo.VBO'


class TestTheGeneratedHierarchy:
    """``OpenGL.raw`` is left out of the pages entirely.

    It is not a hierarchy of modules in the ordinary sense: there are no files,
    only declaration tables that a finder turns into namespaces on demand.
    Every name in it is exported by the module beside it -- `OpenGL.GL.ARB.foo`
    for `OpenGL.raw.GL.ARB.foo` -- which is where the name is declared and
    where a reader should be sent.
    """

    def test_it_is_skipped(self):
        assert 'OpenGL.raw' in dumbpydoc.SKIP_PACKAGES

    def test_nothing_under_it_is_walked(self, monkeypatch):
        monkeypatch.setattr(
            dumbpydoc.pkgutil,
            'walk_packages',
            lambda path, prefix, onerror: [
                (None, prefix + 'GL', True),
                (None, prefix + 'raw', True),
                (None, prefix + 'raw.GL.ARB.foo', False),
            ],
        )
        names = dumbpydoc.package_modules('OpenGL')
        assert 'OpenGL.GL' in names
        assert not [name for name in names if name.startswith('OpenGL.raw')]

    def test_a_name_it_declares_is_claimed_by_the_package_exporting_it(self):
        """`GLfloat` reports `OpenGL.raw.GL._types`, which has no counterpart
        and is not in the set, so the module a reader imports it from takes
        it."""
        target = Fake('OpenGL.raw.GL._types', name='GLfloat')
        shallow = FakeModule('OpenGL.GL', classes=[('GLfloat', target)])
        deep = FakeModule('OpenGL.GL.ARB.imaging', classes=[('GLfloat', target)])
        claims = dumbpydoc.claim_owners([deep, shallow])
        assert claims[('OpenGL.raw.GL._types', 'GLfloat')][0] == 'OpenGL.GL'


class TestSomebodyElsesClass:
    """A package naming another project's class declares the name, not the class.

    ``ArrayType = numpy.ndarray`` is a name OpenGLContext offers, so the page
    carries it; writing the class out under it copies a few thousand lines of
    numpy's own documentation into the page, and numpy documents it already.
    """

    def module(self):
        return FakeModule('OpenGLContext.arrays')

    def test_a_class_from_outside_the_packages_is_named(self):
        import numpy

        assert (
            dumbpydoc.defined_elsewhere(numpy.ndarray, self.module())
            == 'numpy.ndarray'
        )

    def test_a_class_of_ours_is_not(self):
        assert dumbpydoc.defined_elsewhere(Fake('OpenGL.GL'), self.module()) is None

    def test_the_page_says_where_to_read_about_it(self):
        import numpy

        module = FakeModule('OpenGL.arrays', classes=[('ArrayType', numpy.ndarray)])
        page = dumbpydoc.Renderer({}, {}).render(module)
        assert '.. py:class:: ArrayType' in page
        assert 'Another name for :py:class:`numpy.ndarray`.' in page
        assert 'ctypes' not in page


class TestTheIndexPage:
    def test_it_says_what_the_caller_asked_it_to(self, tmp_path):
        """A set with no reference pages beside it says something else."""
        dumbpydoc.write_index(
            ['OpenGLContext'],
            ['OpenGLContext'],
            str(tmp_path),
            title='API reference',
            paragraphs=['A page per module of the engine.'],
        )
        page = (tmp_path / 'index.rst').read_text(encoding='utf-8')
        assert 'A page per module of the engine.' in page
        assert 'reference page' not in page
        assert '   OpenGLContext' in page


class TestPrivateNames:
    def test_the_packages_documented_are_pyopengl_and_its_accelerators(self):
        """OpenGLContext and the rest have documentation of their own."""
        assert dumbpydoc.PROJECTS == ['OpenGL', 'OpenGL_accelerate']

    def test_the_test_suites_are_not_part_of_the_surface(self):
        assert '.tests' in dumbpydoc.SKIP_FRAGMENTS
