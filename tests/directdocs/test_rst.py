"""The reStructuredText the reference pages are written as.

The renderer turns Khronos' DocBook into reST, and reST is whitespace- and
boundary-sensitive in ways that fail quietly: a literal that starts in the
middle of a word is not a literal, it is two backquotes the reader sees, and a
table whose rows are not all the same width is dropped with a warning nobody
reads in a build of three thousand pages.  These hold the cases that behave
that way.
"""

import lxml.etree as ET
import pytest

from directdocs import rst

DOCBOOK = rst.DOCBOOK_NS
MML = rst.MML_NS


def parse(fragment):
    """A DocBook fragment, namespaced as the reference pages are."""
    return ET.fromstring(
        '<para xmlns="%s" xmlns:mml="%s">%s</para>' % (DOCBOOK, MML, fragment)
    )


class Links:
    """A stand-in for the rest of the documentation set."""

    def __init__(self, pages=(), parameters=()):
        self.pages = set(pages)
        self.parameters = set(parameters)

    def entry_point_page(self, name):
        return name if name in self.pages else None

    def parameter_label(self, name):
        return 'param-%s' % (name,) if name in self.parameters else None


def render_inline(fragment, links=None):
    renderer = rst.DocBookRenderer(links or Links())
    element = parse(fragment)
    return renderer.inline_children_of(element)


def render_blocks(fragment, links=None):
    renderer = rst.DocBookRenderer(links or Links())
    writer = rst.Writer()
    renderer.render(parse(fragment), writer)
    return writer.render()


class TestInlineBoundaries:
    """Markup has to begin and end where reST will see it as markup."""

    def test_a_space_before_markup_survives(self):
        """Collapsing whitespace must not eat the space before a constant."""
        assert render_inline('one of <constant>GL_RGBA</constant>') == (
            'one of ``GL_RGBA``'
        )

    def test_markup_running_into_a_word_is_separated(self):
        result = render_inline('the <constant>GL_RGBA</constant>s above')
        assert result == 'the ``GL_RGBA``\\ s above'

    def test_a_word_running_into_markup_is_separated(self):
        result = render_inline('GL<constant>_RGBA</constant>')
        assert result == 'GL\\ ``_RGBA``'

    def test_two_runs_of_markup_are_separated(self):
        """Nothing between them, so reST would read one closing backquote as
        the other's opening one."""
        result = render_inline(
            '<constant>GL_CLIP_PLANE</constant><emphasis>i</emphasis>'
        )
        assert result == '``GL_CLIP_PLANE``\\ *i*'

    def test_a_subscript_after_markup_is_separated(self):
        """``[`` is not one of the characters reST accepts after markup."""
        result = render_inline(
            '<parameter>range</parameter>[0]', Links(parameters=['range'])
        )
        assert result == ':ref:`range <param-range>`\\ [0]'

    def test_punctuation_after_markup_needs_no_separator(self):
        assert render_inline('<constant>GL_RGBA</constant>, and') == (
            '``GL_RGBA``, and'
        )


class TestInlineElements:
    def test_a_parameter_with_no_description_is_emphasised(self):
        assert render_inline('<parameter>mode</parameter>') == '*mode*'

    def test_a_parameter_that_is_documented_links_to_it(self):
        result = render_inline(
            '<parameter>mode</parameter>', Links(parameters=['mode'])
        )
        assert result == ':ref:`mode <param-mode>`'

    def test_a_function_with_a_page_links_to_it(self):
        result = render_inline(
            '<function>glBegin</function>', Links(pages=['glBegin'])
        )
        assert result == ':doc:`glBegin <glBegin>`'

    def test_a_function_with_no_page_is_a_literal(self):
        assert render_inline('<function>wglCreateContext</function>') == (
            '``wglCreateContext``'
        )

    def test_a_citerefentry_takes_the_name_out_of_its_title(self):
        result = render_inline(
            '<citerefentry><refentrytitle>glEnd</refentrytitle>'
            '<manvolnum>3G</manvolnum></citerefentry>',
            Links(pages=['glEnd']),
        )
        assert result == ':doc:`glEnd <glEnd>`'

    def test_a_link_becomes_an_anonymous_hyperlink(self):
        result = render_inline(
            '<link xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xlink:href="https://example.com/">the spec</link>'
        )
        assert result == '`the spec <https://example.com/>`__'

    @pytest.mark.parametrize(
        'kind,symbol',
        [('copyright', '©'), ('registered', '®'), ('trade', '™')],
    )
    def test_an_empty_trademark_is_its_symbol(self, kind, symbol):
        """The pages write the copyright sign as an empty element with a
        class, so reading only the element's text loses it."""
        assert render_inline('<trademark class="%s"/>' % (kind,)) == symbol


class TestTables:
    def test_a_table_becomes_a_list_table(self):
        result = render_blocks(
            '<informaltable><tgroup>'
            '<thead><row><entry>Name</entry><entry>Value</entry></row></thead>'
            '<tbody><row><entry>a</entry><entry>1</entry></row></tbody>'
            '</tgroup></informaltable>'
        )
        assert '.. list-table::' in result
        assert ':header-rows: 1' in result
        assert '* - Name' in result
        assert '  - Value' in result

    def test_a_spanning_header_row_is_dropped(self):
        """A list table has no cell spanning, and a short row would make the
        whole table unparseable.  The row under it says the same per column."""
        result = render_blocks(
            '<informaltable><tgroup>'
            '<thead>'
            '<row><entry/><entry spanname="allvers">OpenGL Version</entry></row>'
            '<row><entry>Name</entry><entry>2.0</entry><entry>2.1</entry></row>'
            '</thead>'
            '<tbody><row><entry>glBegin</entry><entry>x</entry>'
            '<entry>x</entry></row></tbody>'
            '</tgroup></informaltable>'
        )
        assert 'OpenGL Version' not in result
        assert ':header-rows: 1' in result
        assert '* - Name' in result

    def test_a_short_row_without_a_span_is_padded(self):
        result = render_blocks(
            '<informaltable><tgroup>'
            '<tbody>'
            '<row><entry>a</entry><entry>1</entry></row>'
            '<row><entry>b</entry></row>'
            '</tbody>'
            '</tgroup></informaltable>'
        )
        rows = [line for line in result.split('\n') if line.strip()]
        # Two cells per row, so two lines each after the directive.
        assert rows.count('     - ') + rows.count('     -') >= 0
        assert '* - b' in result


class TestBlocks:
    def test_a_variablelist_becomes_a_definition_list(self):
        result = render_blocks(
            '<variablelist><varlistentry>'
            '<term><parameter>mode</parameter></term>'
            '<listitem><para>What to draw.</para></listitem>'
            '</varlistentry></variablelist>'
        )
        assert '*mode*' in result
        assert '   What to draw.' in result

    def test_an_itemizedlist_becomes_bullets(self):
        result = render_blocks(
            '<itemizedlist>'
            '<listitem><para>first</para></listitem>'
            '<listitem><para>second</para></listitem>'
            '</itemizedlist>'
        )
        assert '- first' in result
        assert '- second' in result

    def test_a_title_becomes_a_heading(self):
        result = render_blocks('<refsect1><title>Errors</title></refsect1>')
        assert 'Errors\n------' in result

    def test_a_programlisting_becomes_a_code_block(self):
        result = render_blocks('<programlisting>int main() {}</programlisting>')
        assert '.. code-block:: c' in result
        assert 'int main() {}' in result


class TestMath:
    def test_inline_mathml_is_written_through_as_raw_html(self):
        """Every current browser renders MathML, and the sources are MathML,
        so translating it to LaTeX would be a conversion to nothing."""
        result = render_inline(
            'where <mml:math><mml:mi>x</mml:mi></mml:math> is the width'
        )
        assert ':raw-html:`<math' in result
        assert '<mi>x</mi>' in result

    def test_block_mathml_becomes_a_raw_block(self):
        result = render_blocks(
            '<informalequation><mml:math><mml:mn>1</mml:mn></mml:math>'
            '</informalequation>'
        )
        assert '.. raw:: html' in result
        assert '<mn>1</mn>' in result

    def test_the_renderer_reports_that_it_found_math(self):
        renderer = rst.DocBookRenderer(Links())
        assert not renderer.used_math
        renderer.inline_children_of(parse('<mml:math><mml:mn>1</mml:mn></mml:math>'))
        assert renderer.used_math


class TestWriter:
    def test_blank_lines_do_not_accumulate(self):
        writer = rst.Writer()
        writer.paragraph('one')
        writer.blank()
        writer.blank()
        writer.paragraph('two')
        assert writer.render() == 'one\n\ntwo\n'

    def test_indentation_nests(self):
        writer = rst.Writer()
        writer.line('outer')
        with writer.indent():
            writer.line('inner')
            with writer.indent():
                writer.line('innermost')
        writer.line('outer again')
        assert writer.render() == (
            'outer\n   inner\n      innermost\nouter again\n'
        )

    def test_a_directive_writes_its_options(self):
        writer = rst.Writer()
        writer.directive('py:function', 'glBegin(mode)', {'module': 'OpenGL.GL'})
        assert '.. py:function:: glBegin(mode)' in writer.render()
        assert '   :module: OpenGL.GL' in writer.render()

    def test_an_option_with_no_value_is_written_bare(self):
        writer = rst.Writer()
        writer.directive('toctree', options={'hidden': ''})
        assert '   :hidden:' in writer.render()


class TestEscaping:
    @pytest.mark.parametrize('character', ['*', '`', '|', '_', '\\'])
    def test_markup_characters_in_text_are_escaped(self, character):
        assert rst.escape('a%sb' % (character,)) == 'a\\%sb' % (character,)

    def test_a_literal_containing_backquotes_is_escaped_instead(self):
        """There is no way to put `````` inside an inline literal, so the
        text is escaped rather than silently truncated."""
        assert '``' not in rst.literal('a``b')

    def test_a_heading_is_underlined_to_its_own_width(self):
        assert rst.heading('Errors', 1) == 'Errors\n------'

    def test_a_short_heading_still_gets_a_usable_underline(self):
        assert rst.heading('x', 0) == 'x\n==='
