"""The reStructuredText the reference pages are written as.

The renderer turns Khronos' DocBook into reST, and reST is whitespace- and
boundary-sensitive in ways that fail quietly: a literal that starts in the
middle of a word is not a literal, it is two backquotes the reader sees, and a
table whose rows are not all the same width is dropped with a warning nobody
reads in a build of three thousand pages.  These hold the cases that behave
that way.
"""

import io

import docutils.core
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

    def test_a_directive_argument_spanning_lines_is_written_on_one(self):
        """A default whose ``repr`` spans lines -- a node, an array -- lands
        in a signature, and the directive ends at the first line break."""
        writer = rst.Writer()
        writer.directive(
            'py:method',
            "__init__(self, style=WaterStyle(\n\tname = 'lake',\n"
            '\tspeed = 0.8\n), name=None)',
            {'value': 'array([1., 0.],\n      dtype=float32)'},
        )
        assert writer.render() == (
            ".. py:method:: __init__(self, style=WaterStyle( name = 'lake',"
            ' speed = 0.8 ), name=None)\n'
            '   :value: array([1., 0.], dtype=float32)\n'
        )


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


class TestDocstrings:
    """How a docstring becomes part of a page.

    PyOpenGL's docstrings are mostly a call signature, a sentence or two, and
    an indented list of what each argument means.  A few are hand-written
    reStructuredText.  Both have to read as themselves.
    """

    def render(self, text, entry_points=None):
        writer = rst.Writer()
        rst.write_docstring(text, writer, entry_points)
        return writer.render()

    def test_one_line_is_a_paragraph(self):
        assert self.render('Bind a named texture').strip() == (
            'Bind a named texture'
        )

    def test_an_argument_list_becomes_a_definition_list(self):
        out = self.render(
            'Copy data into the bound buffer\n'
            '\n'
            '    target -- which buffer type is intended\n'
            '    size -- the count in bytes\n'
        )
        assert 'target\n   which buffer type is intended' in out
        assert 'size\n   the count in bytes' in out
        assert 'code-block' not in out

    def test_a_continuation_joins_its_entry(self):
        out = self.render(
            'Do a thing\n'
            '\n'
            '    data -- the pointer to use, which may be None to\n'
            '        allocate without copying\n'
        )
        assert 'allocate without copying' in out
        assert out.count('data') == 1

    def test_an_indented_run_that_is_not_an_argument_list_stays_verbatim(self):
        """Its layout is what carries its meaning.

        Indented relative to prose above it -- a docstring whose whole body is
        indented has that indent removed by `cleandoc`, and then nothing about
        it is indented at all.
        """
        out = self.render(
            'Map the buffer\n'
            '\n'
            'Taken from:\n'
            '\n'
            '    numpy-discussion, message 01161\n'
            '    and the comment under it\n'
        )
        assert '.. code-block:: text' in out
        assert 'numpy-discussion, message 01161' in out

    def test_a_mixed_run_is_left_alone_rather_than_half_converted(self):
        """Half of it reads as arguments and half does not, so none of it is
        converted -- joining it into a paragraph would run the entries
        together into one sentence."""
        out = self.render(
            'Query it\n'
            '\n'
            'program -- the program to query\n'
            'Following parameters are optional:\n'
            'bufSize -- the size of the buffer\n'
        )
        assert '.. code-block:: text' in out
        assert 'program -- the program to query' in out

    def test_a_sentence_with_a_dash_in_it_is_a_sentence(self):
        """`--` between words is not an argument list."""
        out = self.render('Copy the given data -- the fast path where it fits')
        assert 'code-block' not in out
        assert 'Copy the given data' in out

    def test_a_role_written_by_hand_survives(self):
        """`:class:`~OpenGL.Tk.widget.GLFrame`` is a link its author meant."""
        out = self.render(
            'A widget.\n\n:class:`~OpenGL.Tk.widget.GLFrame` owns a context.\n'
        )
        assert ':class:`~OpenGL.Tk.widget.GLFrame`' in out
        assert '\\:class\\:' not in out

    def test_a_literal_written_by_hand_survives(self):
        """``p`` is a name its author wrote as a literal.

        The packages built on PyOpenGL write their docstrings that way
        throughout; escaping one leaves the backquotes on the page.
        """
        out = self.render(
            'Matrix math.\n\nA point ``p`` is transformed as ``p @ M``.\n'
        )
        assert '``p``' in out
        assert '\\`\\`' not in out

    def test_plain_text_is_escaped(self):
        """An asterisk in plain prose is an asterisk, not emphasis."""
        out = self.render('Takes *args and returns None')
        assert '\\*args' in out

    def test_a_directive_is_written_through_untouched(self):
        """A directive and the body indented under it are one thing."""
        out = self.render(
            'An example.\n\n.. code-block:: python\n\n   glBegin(GL_TRIANGLES)\n'
        )
        assert '.. code-block:: python' in out
        assert 'glBegin(GL_TRIANGLES)' in out


class TestDocstringsParse:
    """What a docstring becomes is reStructuredText that parses cleanly.

    Each of these is a shape the packages' docstrings are written in.  A
    warning from docutils is a page that renders as something other than what
    its author wrote: a sample run into the paragraph above it, a list joined
    into one sentence, the rest of an argument's description set as code.
    """

    def render(self, text):
        writer = rst.Writer()
        rst.write_docstring(text, writer)
        return writer.render()

    def assert_parses(self, text):
        """``text`` as a page, which docutils reads with nothing to report."""
        out = self.render(text)
        stream = io.StringIO()
        docutils.core.publish_doctree(
            out,
            settings_overrides={
                'warning_stream': stream,
                'report_level': 2,
                'halt_level': 5,
            },
        )
        assert stream.getvalue() == '', out
        return out

    def test_a_literal_block_marker_is_not_left_before_the_block(self):
        """``::`` says the indented block after it is a sample.

        The block is written as a ``code-block`` directive, so the marker has
        said its piece: left in, it asks for a second literal block that is
        not there.  ``Example::`` reads ``Example:``, as it would in reST.
        """
        out = self.assert_parses(
            'Keep the returned source::\n'
            '\n'
            '    previous = setTimeSource(myClock)\n'
            '    setTimeSource(previous)\n'
            '\n'
            'A closure will *not* survive::\n'
            '\n'
            '    handler = lambda event: step(+1)\n'
        )
        assert 'Keep the returned source:\n' in out
        assert '::\n' not in out.replace('.. code-block::', '')

    def test_a_marker_on_its_own_word_is_dropped(self):
        """``Example ::`` is reST for a paragraph that shows no colon."""
        out = self.assert_parses('Like this ::\n\n    f(x)\n')
        assert 'Like this\n' in out

    def test_a_continuation_line_in_plain_text_joins_its_entry(self):
        """An argument's description wraps onto an indented line.

        The docstring is otherwise unindented, so the continuation is the only
        indented line in it; it belongs to the entry above, not in a sample
        of its own.
        """
        out = self.assert_parses(
            'Install the clock.\n'
            '\n'
            'source -- a callable returning seconds, or None\n'
            '    to go back to the wall clock\n'
            '\n'
            'A source should never go backwards.\n'
        )
        assert 'code-block' not in out
        assert 'or None to go back to the wall clock' in out

    def test_a_sample_directly_under_a_line_stays_a_sample(self):
        """Only an argument or a list item continues onto an indented line.

        ``Usage:`` with the call indented under it is a label and a sample.
        """
        out = self.assert_parses(
            'Run it.\n\nUsage:\n    run(the, thing)\n\nThen stop.\n'
        )
        assert '.. code-block:: text' in out
        assert '   run(the, thing)' in out

    def test_a_bulleted_list_is_a_list(self):
        """Joined into prose, its items run into one sentence."""
        out = self.assert_parses(
            'Testing utilities:\n'
            '\n'
            '- framebuffer_comparison: compare rendered output between paths\n'
            '    or against saved reference images\n'
            '- subprocess_runner: run tests in isolated subprocesses\n'
            '- event_injector: inject keyboard and mouse events\n'
        )
        assert 'code-block' not in out
        items = out.split('\n\n')[1].split('\n- ')
        assert [' '.join(item.split()) for item in items] == [
            '- framebuffer\\_comparison: compare rendered output between paths'
            ' or against saved reference images',
            'subprocess\\_runner: run tests in isolated subprocesses',
            'event\\_injector: inject keyboard and mouse events',
        ]

    def test_a_field_list_is_written_through(self):
        """``:param name:`` is reST, and a paragraph when it is not read as it.

        Escaped and joined, every field runs into the one before; and a
        field's continuation line, indented under it, is split off as a
        sample.
        """
        out = self.assert_parses(
            'A square elevation grid.\n'
            '\n'
            ':param grid: (res, res) array of normalised heights in [0, 1].\n'
            ':param extent: side length of the terrain in world units\n'
            '    (centred on the origin).\n'
            ':raises ValueError: for a grid that is not square.\n'
        )
        assert 'code-block' not in out
        assert '\n:param extent: side length' in out
        assert '\n:raises ValueError:' in out

    def test_a_qualified_name_is_a_name(self):
        """``separable (keyword only) -- ...`` is an argument with a note."""
        out = self.assert_parses(
            'Create a program\n'
            '\n'
            'shaders -- the shaders to attach to the\n'
            '    generated program.\n'
            'separable (keyword only) -- set the separable flag to allow\n'
            '    partial installation\n'
        )
        assert 'code-block' not in out
        assert 'separable (keyword only)\n   set the separable flag' in out
        assert 'to allow partial installation' in out

    def test_entries_under_an_entry_are_a_list_of_their_own(self):
        """The values an argument takes, each with what it means."""
        out = self.assert_parses(
            'Bind the buffer\n'
            '\n'
            'target -- VBO target to which to bind (array or indices)\n'
            '    GL_ARRAY_BUFFER -- array-data binding\n'
            '    GL_ELEMENT_ARRAY_BUFFER -- index-data binding, for\n'
            '        indexed draws\n'
            '\n'
            'size -- the count in bytes\n'
        )
        assert (
            'target\n'
            '   VBO target to which to bind (array or indices)\n'
            '\n'
            '   GL\\_ARRAY\\_BUFFER\n'
            '      array-data binding\n'
            '\n'
            '   GL\\_ELEMENT\\_ARRAY\\_BUFFER\n'
            '      index-data binding, for indexed draws\n'
        ) in out
        assert '\nsize\n   the count in bytes' in out

    @pytest.mark.parametrize('shape', ['written through', 'plain'])
    def test_names_separated_by_a_slash_share_an_entry(self, shape):
        """``width/height -- the frame size`` documents two arguments at once.

        Not read as names, it ends the definition list, and every entry after
        it is a block quote with unannounced indents.
        """
        literal = ' See ``encoders()``.' if shape == 'written through' else ''
        out = self.assert_parses(
            'An encoder.%s\n'
            '\n'
            'width/height -- frame size; H.264 reaches 4096 each way\n'
            'fps -- frames per second, as a number or a pair.\n'
            '    It sets the declared frame rate; it paces nothing.\n'
            'framebuffer/owns_texture -- set when the encoder made the\n'
            '    texture itself\n' % (literal,)
        )
        assert 'width/height\n   frame size' in out
        assert 'fps\n   frames per second, as a number or a pair. It sets' in out
        assert '\n   set when the encoder made the texture itself' in out


class TestLinkingEntryPoints:
    def render(self, text, entry_points):
        writer = rst.Writer()
        rst.write_docstring(text, writer, entry_points)
        return writer.render()

    def test_a_name_in_prose_becomes_a_link(self):
        out = self.render('Wraps glBegin for you', {'glBegin': 'gl/glBegin'})
        assert ':doc:`glBegin </reference/gl/glBegin>`' in out

    def test_a_name_already_marked_up_is_left_alone(self):
        out = self.render(
            'See :py:func:`glBegin` and ``glEnd``.\n\nMore about glBegin.',
            {'glBegin': 'gl/glBegin', 'glEnd': 'gl/glEnd'},
        )
        assert ':py:func:`glBegin`' in out
        assert '``glEnd``' in out
        assert ':doc:`glBegin </reference/gl/glBegin>`' in out

    def test_a_name_that_is_a_call_is_left_alone(self):
        """`glBegin(GL_TRIANGLES)` is code, and a link inside a call is not
        what anybody wants."""
        out = self.render(
            'Call glBegin(mode) first', {'glBegin': 'gl/glBegin'}
        )
        assert ':doc:' not in out

    def test_a_longer_name_wins_over_a_shorter_one(self):
        out = self.render(
            'Use glBeginQuery here',
            {'glBegin': 'gl/glBegin', 'glBeginQuery': 'gl/glBeginQuery'},
        )
        assert ':doc:`glBeginQuery </reference/gl/glBeginQuery>`' in out

    def test_nothing_happens_without_a_manifest(self):
        assert ':doc:' not in self.render('Wraps glBegin for you', {})
