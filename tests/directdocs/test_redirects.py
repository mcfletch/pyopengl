#! /usr/bin/env python3
"""Stub pages at the 3.x URLs, pointing at where each page is now.

The 3.x site published a page per entry point at
``documentation/manual/<name>.html``, and those URLs are bookmarked, linked to
and indexed.  The set has a page for each of them, at a different address, so
every old URL gets a stub that sends a reader to the new one.
"""

import os

from directdocs import redirects


class TestResolvingAnOldName:
    PAGES = frozenset(
        {
            'gl/glBeginTransformFeedback',
            'gl/glBeginQueryIndexed_glEndQueryIndexed',
            'gl/glGet',
            'glu/gluPerspective',
            'glut/glutInit',
            'gles1/glDrawTex',
            'gles3/glBlendBarrier',
        }
    )
    ENTRY_POINTS = {'glBeginTransformFeedback': 'gl/glBeginTransformFeedback'}

    def resolve(self, name):
        return redirects.resolve(name, self.ENTRY_POINTS, self.PAGES)

    def test_an_entry_point_goes_to_the_page_that_documents_it(self):
        assert self.resolve('glBeginTransformFeedback') == (
            'gl/glBeginTransformFeedback'
        )

    def test_a_page_named_for_a_family_is_found_by_its_own_name(self):
        """``glGet`` is a page, not an entry point, so the manifest has no key."""
        assert self.resolve('glGet') == 'gl/glGet'

    def test_a_comma_in_the_old_name_is_the_joined_page(self):
        """The 3.x file is ``glBeginQueryIndexed, glEndQueryIndexed.html``."""
        assert self.resolve('glBeginQueryIndexed, glEndQueryIndexed') == (
            'gl/glBeginQueryIndexed_glEndQueryIndexed'
        )

    def test_glu_and_glut_are_searched(self):
        assert self.resolve('gluPerspective') == 'glu/gluPerspective'
        assert self.resolve('glutInit') == 'glut/glutInit'

    def test_an_es_only_page_is_found_after_the_desktop_apis(self):
        """The 3.x manual carried a few; the set documents them under ES."""
        assert self.resolve('glDrawTex') == 'gles1/glDrawTex'
        assert self.resolve('glBlendBarrier') == 'gles3/glBlendBarrier'

    def test_a_name_with_no_page_anywhere_is_unresolved(self):
        assert self.resolve('glNoSuchThing') is None


class TestTheStubItself:
    def test_it_redirects_without_javascript(self):
        html = redirects.stub('glBegin', '../../reference/gl/glBegin.html')
        assert '<meta http-equiv="refresh"' in html
        assert 'url=../../reference/gl/glBegin.html' in html

    def test_it_carries_a_link_for_a_reader_the_redirect_does_not_move(self):
        html = redirects.stub('glBegin', '../../reference/gl/glBegin.html')
        assert '<a href="../../reference/gl/glBegin.html">' in html

    def test_it_names_the_page_it_is_sending_you_to(self):
        html = redirects.stub('glBegin', '../../reference/gl/glBegin.html')
        assert 'glBegin' in html

    def test_it_is_not_indexed(self):
        """A stub competing with the page it points at is worse than no stub."""
        html = redirects.stub('glBegin', '../../reference/gl/glBegin.html')
        assert 'noindex' in html

    def test_the_target_is_escaped(self):
        html = redirects.stub('x', '../../reference/gl/a&b.html')
        assert 'a&amp;b.html' in html
        assert 'a&b.html' not in html


class TestWritingThem:
    def test_each_old_url_gets_a_file(self, tmp_path):
        written = redirects.write_redirects(
            str(tmp_path),
            names=['glBeginTransformFeedback'],
            entry_points={'glBeginTransformFeedback': 'gl/glBeginTransformFeedback'},
            pages={'gl/glBeginTransformFeedback'},
            narrative={},
        )
        stub = tmp_path / 'documentation' / 'manual' / 'glBeginTransformFeedback.html'
        assert stub.is_file()
        assert written == 1
        assert '../../reference/gl/glBeginTransformFeedback.html' in stub.read_text(
            encoding='utf-8'
        )

    def test_the_old_file_name_is_kept_exactly(self, tmp_path):
        """The URL is what is bookmarked, spaces and commas included."""
        redirects.write_redirects(
            str(tmp_path),
            names=['glBeginQueryIndexed, glEndQueryIndexed'],
            entry_points={},
            pages={'gl/glBeginQueryIndexed_glEndQueryIndexed'},
            narrative={},
        )
        stub = (
            tmp_path / 'documentation' / 'manual'
            / 'glBeginQueryIndexed, glEndQueryIndexed.html'
        )
        assert stub.is_file()

    def test_a_narrative_page_is_written_where_it_is_named(self, tmp_path):
        redirects.write_redirects(
            str(tmp_path),
            names=[],
            entry_points={},
            pages=set(),
            narrative={'documentation/installation.html': 'installation'},
        )
        stub = tmp_path / 'documentation' / 'installation.html'
        assert stub.is_file()
        assert '../installation.html' in stub.read_text(encoding='utf-8')

    def test_a_name_with_nowhere_to_go_lands_on_the_reference_index(self, tmp_path):
        redirects.write_redirects(
            str(tmp_path),
            names=['glNoSuchThing'],
            entry_points={},
            pages=set(),
            narrative={},
        )
        stub = tmp_path / 'documentation' / 'manual' / 'glNoSuchThing.html'
        assert '../../reference/index.html' in stub.read_text(encoding='utf-8')


class TestTheListOfOldPages:
    def test_it_ships_with_the_generator(self):
        assert os.path.isfile(redirects.LEGACY_PAGES)

    def test_it_holds_the_pages_the_3_x_site_published(self):
        names = redirects.legacy_names()
        assert 'glBeginTransformFeedback' in names
        assert 'glBeginQueryIndexed, glEndQueryIndexed' in names
        assert len(names) > 600

    def test_nothing_in_it_is_an_html_file_name(self):
        """The names are page names; the writer adds the suffix."""
        assert not [name for name in redirects.legacy_names() if name.endswith('.html')]
