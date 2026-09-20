"""Reading a Khronos reference page.

The DocBook the pages are written in carries three things that are easy to
lose without noticing, because losing each of them produces a page that builds
cleanly and is missing something: the entity sets, the XIncluded version
tables, and the section ids that say what a section is.
"""

import os

import lxml.etree as ET
import pytest

from childenv import json_from_child
from directdocs import generate


@pytest.fixture
def pages(tmp_path):
    """A directory of DocBook that stands in for one of Khronos' API sets."""
    (tmp_path / 'math.ent').write_text(
        '<!ENTITY times "&#215;">\n<!ENTITY delta "&#948;">\n',
        encoding='utf-8',
    )
    return tmp_path


def write(directory, name, body):
    path = directory / name
    path.write_text(body, encoding='utf-8')
    return str(path)


class TestSectionKind:
    """Which reference section is which, from its id."""

    @pytest.mark.parametrize(
        'id,kind',
        [
            ('parameters', 'parameters'),
            ('parameters2', 'parameters'),
            ('glBegin-parameters', 'parameters'),
            ('seealso', 'seealso'),
            ('glBegin-see_also', 'seealso'),
            ('Copyright', 'copyright'),
            ('copyright', 'copyright'),
            ('versions', 'versions'),
            ('description', 'description'),
        ],
    )
    def test_the_id_says_what_the_section_is(self, id, kind):
        assert generate.section_kind(id) == kind

    def test_an_unknown_id_is_not_a_kind(self):
        assert generate.section_kind('glBegin-examples-of-misuse') is None

    def test_no_id_is_not_a_kind(self):
        assert generate.section_kind(None) is None


class TestEntities:
    """The pages declare their entity sets in a DOCTYPE that has to be
    replaced, and replacing it without them turns `&times;` into an error or,
    worse, into nothing."""

    def test_an_entity_arrives_as_its_character(self, pages):
        path = write(
            pages,
            'glThing.xml',
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE refentry [ <!ENTITY %% mathent SYSTEM "math.ent"> '
            '%%mathent; ]>\n'
            '<refentry xmlns="%s" xml:id="glThing">'
            '<para>two &times; three</para></refentry>' % (generate.DOCBOOK_NS,),
        )
        tree = generate.load_file(path)
        assert '×' in ET.tostring(tree, encoding='unicode')

    def test_a_name_the_iso_sets_lack_is_supplied(self, pages):
        """`mdash` is used by the GLUT pages and is in none of the sets."""
        path = write(
            pages,
            'glutThing.xml',
            '<refentry xmlns="%s" xml:id="glutThing">'
            '<para>a &mdash; b</para></refentry>' % (generate.DOCBOOK_NS,),
        )
        tree = generate.load_file(path)
        assert '—' in ET.tostring(tree, encoding='unicode')


class TestIncludes:
    """The version-support table is assembled out of two XIncludes whose
    XPointer lxml does not evaluate for itself."""

    def test_all_children_are_included(self, pages):
        write(
            pages,
            'head.xml',
            '<?xml version="1.0"?>\n'
            '<funchead xmlns="%s"><thead><row><entry>Version</entry></row>'
            '</thead></funchead>' % (generate.DOCBOOK_NS,),
        )
        path = write(
            pages,
            'glThing.xml',
            '<refentry xmlns="%s" xmlns:xi="%s" xml:id="glThing"><informaltable>'
            '<tgroup><xi:include href="head.xml" xpointer="xpointer(/*/*)"/>'
            '</tgroup></informaltable></refentry>'
            % (generate.DOCBOOK_NS, generate.XINCLUDE_NS),
        )
        tree = generate.load_file(path)
        assert 'Version' in ET.tostring(tree, encoding='unicode')

    def test_a_role_selects_one_row(self, pages):
        write(
            pages,
            'version.xml',
            '<?xml version="1.0"?>\n'
            '<apiversion xmlns="%s">'
            '<row role="20"><entry>two-oh</entry></row>'
            '<row role="46"><entry>four-six</entry></row>'
            '</apiversion>' % (generate.DOCBOOK_NS,),
        )
        path = write(
            pages,
            'glThing.xml',
            '<refentry xmlns="%s" xmlns:xi="%s" xml:id="glThing"><informaltable>'
            '<tgroup><tbody><row><entry>glThing</entry>'
            '<xi:include href="version.xml" '
            'xpointer="xpointer(/*/*[@role=\'46\']/*)"/>'
            '</row></tbody></tgroup></informaltable></refentry>'
            % (generate.DOCBOOK_NS, generate.XINCLUDE_NS),
        )
        tree = generate.load_file(path)
        text = ET.tostring(tree, encoding='unicode')
        assert 'four-six' in text
        assert 'two-oh' not in text

    def test_an_include_with_no_xpointer_brings_the_whole_element(self, pages):
        """A table included this way has to arrive as a table.

        The format tables -- which buffer binding targets exist, which internal
        formats are sized -- are included with no XPointer, and that means the
        document element.  Taking its children instead drops the
        `informaltable` and every cell renders as a paragraph.
        """
        write(
            pages,
            'bindings.xml',
            '<?xml version="1.0"?>\n'
            '<informaltable xmlns="%s"><tgroup><tbody>'
            '<row><entry>GL_ARRAY_BUFFER</entry><entry>Vertex attributes</entry></row>'
            '</tbody></tgroup></informaltable>' % (generate.DOCBOOK_NS,),
        )
        path = write(
            pages,
            'glThing.xml',
            '<refentry xmlns="%s" xmlns:xi="%s" xml:id="glThing">'
            '<para>one of:</para><xi:include href="bindings.xml"/>'
            '</refentry>' % (generate.DOCBOOK_NS, generate.XINCLUDE_NS),
        )
        tree = generate.load_file(path)
        tables = tree.xpath(
            './/d:informaltable', namespaces={'d': generate.DOCBOOK_NS}
        )
        assert len(tables) == 1
        assert 'GL_ARRAY_BUFFER' in ET.tostring(tables[0], encoding='unicode')

    def test_an_include_that_is_not_there_leaves_the_page_readable(self, pages):
        path = write(
            pages,
            'glThing.xml',
            '<refentry xmlns="%s" xmlns:xi="%s" xml:id="glThing">'
            '<para>before<xi:include href="absent.xml"/>after</para>'
            '</refentry>' % (generate.DOCBOOK_NS, generate.XINCLUDE_NS),
        )
        tree = generate.load_file(path)
        text = ET.tostring(tree, encoding='unicode')
        assert 'before' in text and 'after' in text


class TestPageNames:
    """A page name has to work as a filename and as part of a URL."""

    def test_an_ordinary_name_is_left_alone(self):
        assert generate.page_name('glBegin') == 'glBegin'

    def test_a_name_with_two_entry_points_is_made_safe(self):
        assert generate.page_name('glBeginQueryIndexed, glEndQueryIndexed') == (
            'glBeginQueryIndexed_glEndQueryIndexed'
        )


class TestWhichApiAPageBelongsTo:
    """The same file name is a different entry point in each directory.

    ``glTexImage2D.xml`` is in the desktop pages and in three ES directories,
    and they describe different calls -- the desktop one takes arguments ES has
    never had.  Filing them all under GL, which is what reading only the name
    prefix does, loses every ES page whose name a desktop page also uses.
    """

    @pytest.mark.parametrize(
        'name,prefix',
        [
            ('glutInit', 'glut'),
            ('gluOrtho2D', 'glu'),
            ('glXCreateContext', 'glX'),
            ('gleLathe', 'gle'),
            ('glBegin', 'gl'),
            ('eglInitialize', 'egl'),
            ('wglCreateContext', 'wgl'),
        ],
    )
    def test_the_longest_prefix_wins(self, name, prefix):
        assert generate.entry_prefix(name) == prefix

    def test_a_name_that_is_no_entry_point_has_no_prefix(self):
        assert generate.entry_prefix('apiversion.xml') is None

    @pytest.mark.parametrize(
        'directory,name,key',
        [
            ('gl4', 'glBindTexture.xml', 'gl'),
            ('gl2.1', 'glBegin.xml', 'gl'),
            ('es1.1', 'glBindTexture.xml', 'gles1'),
            ('es2.0', 'glBindTexture.xml', 'gles2'),
            ('es3', 'glBindTexture.xml', 'gles3'),
            ('es3.1', 'glDispatchCompute.xml', 'gles3'),
            # These say which API they are whatever directory they sit in.
            ('gl2.1', 'gluOrtho2D.xml', 'glu'),
            ('gl2.1', 'glXCreateContext.xml', 'glx'),
        ],
    )
    def test_the_directory_decides_for_a_gl_page(self, directory, name, key):
        api = generate.api_of_page(directory, name)
        assert api is not None and api.key == key

    def test_a_file_that_is_not_a_reference_page_belongs_nowhere(self):
        assert generate.api_of_page('gl4', 'apiversion.xml') is None


class TestTheApiTable:
    def test_every_key_is_used_once(self):
        keys = [api.key for api in generate.APIS]
        assert len(keys) == len(set(keys))

    def test_every_api_names_a_package_of_its_own(self):
        modules = [api.module for api in generate.APIS]
        assert len(modules) == len(set(modules))

    def test_the_gl_source_directories_are_all_declared(self):
        """A directory the scan reads but no API claims writes no pages."""
        unclaimed = set(generate.REFPAGE_SETS) - set(generate.GL_SOURCE_APIS)
        assert not unclaimed

    def test_egl_and_wgl_have_no_reference_pages(self):
        """Khronos publishes none, so their indexes are built from the
        packages instead."""
        assert generate.BY_KEY['egl'].sources == ()
        assert generate.BY_KEY['wgl'].sources == ()


class TestCrossReferences:
    """A see-also names an entry point; which page it means depends on who is
    asking."""

    def section(self, key, title):
        section = generate.RefSect(generate.BY_KEY[key])
        section.title = section.name = title
        section.id = title
        return section

    def reference(self, *sections):
        reference = generate.Reference()
        for section in sections:
            section.reference = reference
            reference.append(section)
        return reference

    def test_the_asking_api_is_preferred(self):
        desktop = self.section('gl', 'glBindTexture')
        embedded = self.section('gles3', 'glBindTexture')
        asking = self.section('gles3', 'glTexImage2D')
        reference = self.reference(desktop, embedded, asking)
        assert reference.get_crossref('glBindTexture', section=asking) is embedded

    def test_another_api_will_do_where_the_asking_one_has_no_page(self):
        desktop = self.section('gl', 'glBegin')
        asking = self.section('glu', 'gluBeginCurve')
        reference = self.reference(desktop, asking)
        assert reference.get_crossref('glBegin', section=asking) is desktop

    def test_a_name_nothing_has_resolves_to_nothing(self):
        asking = self.section('gl', 'glBegin')
        reference = self.reference(asking)
        assert reference.get_crossref('wglCreateContext', section=asking) is None

    def test_the_docname_carries_the_api(self):
        section = self.section('gles3', 'glBindTexture')
        reference = self.reference(section)
        assert reference.docname(section) == '/reference/gles3/glBindTexture'


#: What `generate.py` answers when it is the first thing in the process to
#: import OpenGL, which is how it runs: `build-docs.py` starts it as a child.
#: The module sets ``PYOPENGL_MODULE_ANNOTATIONS`` as it is imported, and that
#: is read once, when OpenGL is first imported -- so a pytest process, which
#: imported OpenGL long before reaching this file, is not where the question
#: can be asked.
DECLARED_IN = '''
import json

from directdocs import generate

api = generate.BY_KEY['gl']
print(json.dumps(
    None
    if generate.imported_package(api) is None
    else {
        name: generate.declaring_module(api, name)
        for name in ('glBegin', 'glColorPointerb')
    }
))
'''


@pytest.fixture(scope='module')
def declared():
    """What a run of ``generate.py`` says each entry point was declared by."""
    answered = json_from_child(DECLARED_IN)
    if answered is None:
        pytest.skip('OpenGL.GL will not import here')
    return answered


class TestWhereAnEntryPointIsDeclared:
    """An API index links every entry point Khronos publishes no page for.

    The link has to name one target.  A bare name would be searched for, and
    seventy-six of desktop OpenGL's extension entry points share a name with an
    ES one, so the search finds two and links to neither.
    """

    def test_an_entry_point_names_the_module_it_came_from(self, declared):
        assert declared['glBegin'] == 'OpenGL.GL.VERSION.GL_1_0'

    def test_a_decorated_form_names_the_package_that_has_it(self, declared):
        """`glColorPointerb` is built in `OpenGL.GL.pointers` and put into the
        package, keeping the `__module__` of the entry point it decorates --
        which is a module that does not have it."""
        assert declared['glColorPointerb'] == 'OpenGL.GL'

    def test_a_name_the_package_does_not_have_falls_back_to_it(self):
        api = generate.BY_KEY['gl']
        if generate.imported_package(api) is None:
            pytest.skip('OpenGL.GL will not import here')
        assert generate.declaring_module(api, 'glNoSuchThing') == 'OpenGL.GL'

    def test_a_package_that_will_not_import_still_answers(self, monkeypatch):
        monkeypatch.setattr(generate, 'imported_package', lambda api: None)
        api = generate.BY_KEY['wgl']
        assert generate.declaring_module(api, 'wglCreateContext') == 'OpenGL.WGL'


class TestRefpageSets:
    """The API directories to scan.  Naming one that does not exist reads as
    "that API has no pages" rather than as a mistake, which is how `es3.1`
    went unscanned behind a typo."""

    def test_every_named_set_exists_in_the_checkout(self):
        if not os.path.isdir(generate.REFPAGES):
            pytest.skip('no OpenGL-Refpages checkout; run acquireoriginal.py')
        missing = [
            name
            for name in generate.REFPAGE_SETS
            if not os.path.isdir(os.path.join(generate.REFPAGES, name))
        ]
        assert not missing, 'named but absent: %s' % (', '.join(missing),)
