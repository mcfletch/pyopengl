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
    def test_an_entry_point_with_a_reference_page_links_to_it(self):
        renderer = dumbpydoc.Renderer({'glBegin': 'glBegin'}, {})
        assert renderer.reference_link('glBegin') == (
            ':doc:`glBegin </reference/glBegin>`'
        )

    def test_an_alias_links_to_the_page_that_documents_it(self):
        """`glColor3f` is documented on `glColor`."""
        renderer = dumbpydoc.Renderer({'glColor3f': 'glColor'}, {})
        assert renderer.reference_link('glColor3f') == (
            ':doc:`glColor3f </reference/glColor>`'
        )

    def test_a_name_with_no_page_has_no_link(self):
        assert dumbpydoc.Renderer({}, {}).reference_link('glGenBuffersARB') is None


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


class TestFoldingTheGeneratedModules:
    """Every extension exists twice, and only one of the pair has content.

    ``OpenGL.GL.ARB.foo`` is what a program imports; ``OpenGL.raw.GL.ARB.foo``
    is the generated declarations it is built from.  They share their names and
    one module declares each, so the raw half of nearly every pair would have a
    page saying only that its names are documented elsewhere -- thirteen
    hundred of them.
    """

    def pair(self, declared_by_raw=()):
        target = Fake('OpenGL.raw.GL.ARB.foo')
        raw = FakeModule(
            'OpenGL.raw.GL.ARB.foo',
            functions=[('glFooARB', target)],
            constants=[(name, Fake('OpenGL.raw.GL.ARB.foo')) for name in declared_by_raw],
        )
        friendly = FakeModule(
            'OpenGL.GL.ARB.foo', functions=[('glFooARB', target)]
        )
        return raw, friendly

    def folded_for(self, modules, entry_points=None):
        renderer = dumbpydoc.Renderer(
            entry_points or {}, dumbpydoc.claim_owners(modules)
        )
        return dumbpydoc.fold_generated_modules(modules, renderer), renderer

    def test_a_raw_module_with_nothing_of_its_own_is_folded(self):
        raw, friendly = self.pair()
        folded, _ = self.folded_for([raw, friendly])
        assert folded == {'OpenGL.raw.GL.ARB.foo': 'OpenGL.GL.ARB.foo'}

    def test_a_raw_module_that_declares_something_keeps_its_page(self):
        """`OpenGL.raw.GL._types` and its neighbours define names that exist
        nowhere else."""
        raw, friendly = self.pair(declared_by_raw=['GL_FOO_ARB'])
        folded, _ = self.folded_for([raw, friendly])
        assert folded == {}

    def test_a_raw_module_with_no_counterpart_keeps_its_page(self):
        raw, _friendly = self.pair()
        folded, _ = self.folded_for([raw])
        assert folded == {}

    def test_a_package_waits_for_its_children(self):
        """A raw package is only folded once everything under it is."""
        raw, friendly = self.pair(declared_by_raw=['GL_FOO_ARB'])
        raw_package = FakeModule('OpenGL.raw.GL.ARB')
        raw_package.modules = ['OpenGL.raw.GL.ARB.foo']
        friendly_package = FakeModule('OpenGL.GL.ARB')
        folded, _ = self.folded_for([raw, friendly, raw_package, friendly_package])
        assert 'OpenGL.raw.GL.ARB' not in folded

    def test_a_package_whose_children_are_all_folded_goes_too(self):
        raw, friendly = self.pair()
        raw_package = FakeModule('OpenGL.raw.GL.ARB')
        raw_package.modules = ['OpenGL.raw.GL.ARB.foo']
        friendly_package = FakeModule('OpenGL.GL.ARB')
        folded, _ = self.folded_for([raw, friendly, raw_package, friendly_package])
        assert folded['OpenGL.raw.GL.ARB'] == 'OpenGL.GL.ARB'

    def test_the_carrying_page_declares_the_folded_module(self):
        """So a reference to it still resolves, and the module index still
        lists it -- leading to where the content is."""
        raw, friendly = self.pair()
        folded, renderer = self.folded_for([raw, friendly])
        renderer.folded = folded
        page = renderer.render(friendly)
        assert '.. py:module:: OpenGL.raw.GL.ARB.foo' in page
        assert 'Generated declarations' in page

    def test_the_declaration_comes_last(self):
        """`py:module` sets which module the directives after it belong to."""
        raw, friendly = self.pair()
        folded, renderer = self.folded_for([raw, friendly])
        renderer.folded = folded
        page = renderer.render(friendly)
        assert page.rstrip().endswith('.. py:module:: OpenGL.raw.GL.ARB.foo')

    def test_a_folded_module_is_not_named_in_a_toctree(self):
        """It has no page, so naming it would be a broken link."""
        raw, friendly = self.pair()
        raw_package = FakeModule('OpenGL.raw.GL.ARB')
        raw_package.modules = ['OpenGL.raw.GL.ARB.foo']
        friendly_package = FakeModule('OpenGL.GL.ARB')
        folded, renderer = self.folded_for(
            [raw, friendly, raw_package, friendly_package]
        )
        renderer.folded = folded
        page = renderer.render(raw_package)
        assert 'OpenGL.raw.GL.ARB.foo' not in page.split('Generated declarations')[0]


class TestPrivateNames:
    def test_the_packages_documented_are_pyopengl_and_its_accelerators(self):
        """OpenGLContext and the rest have documentation of their own."""
        assert dumbpydoc.PROJECTS == ['OpenGL', 'OpenGL_accelerate']

    def test_the_test_suites_are_not_part_of_the_surface(self):
        assert '.tests' in dumbpydoc.SKIP_FRAGMENTS
