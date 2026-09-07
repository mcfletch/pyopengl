"""The markup directdocs reads out of tutorial commentary."""
from directdocs.dumbmarkup import Anchor, Image, Paragraph


def children_of(text):
    return Paragraph(text).children


class TestBracketedMarkup:
    """``[target text]`` in a commentary block."""

    def test_a_filename_becomes_an_image(self):
        (child,) = children_of('[shadow_1.py-screen-0001.png Screenshot]')
        assert isinstance(child, Image)
        assert child.url == 'shadow_1.py-screen-0001.png'
        assert child.text == 'Screenshot'

    def test_a_url_becomes_a_link(self):
        (child,) = children_of('[http://example.com/smt.html this C tutorial]')
        assert isinstance(child, Anchor)
        assert not isinstance(child, Image)
        assert child.url == 'http://example.com/smt.html'

    def test_prose_in_brackets_is_left_alone(self):
        assert children_of('run it with [--help for the tunable knobs]') == []

    def test_a_class_prefix_styles_the_image(self):
        (child,) = children_of(
            '[class=clear-right transforms_1.py-screen-0009.png Perspective]')
        assert isinstance(child, Image)
        assert child.url == 'transforms_1.py-screen-0009.png'
        assert child.text == 'Perspective'
        assert 'clear-right' in child.html_class

    def test_a_class_prefix_styles_a_link(self):
        (child,) = children_of('[class=external http://example.com/ Example]')
        assert isinstance(child, Anchor)
        assert not isinstance(child, Image)
        assert child.url == 'http://example.com/'
        assert 'external' in child.html_class

    def test_two_images_run_together(self):
        first, second = children_of(
            '[class=clear-right a.png One][b.png Two]')
        assert (first.url, second.url) == ('a.png', 'b.png')
        assert 'clear-right' in first.html_class
        assert 'clear-right' not in second.html_class
