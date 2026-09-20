"""Reading a Khronos reference page.

The DocBook the pages are written in carries three things that are easy to
lose without noticing, because losing each of them produces a page that builds
cleanly and is missing something: the entity sets, the XIncluded version
tables, and the section ids that say what a section is.
"""

import os

import lxml.etree as ET
import pytest

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
