"""Tier 3 (c): the image family.

An image's length is a function of its format, its type, its dimensions and
the current pixel-store state, and the tables that decide it are extensible at
run time -- ``OpenGL.images.registerImage`` is a public entry point third
parties use for their own formats.  So the C owns the call and the sizing
stays in Python, which is the same line the arrays rule draws.

What the generator has to work out is which arguments carry the format, the
type and the dimensions.  The registry says, in the ``COMPSIZE`` on the pixels
parameter.
"""

import os

import pytest

from cdispatch import emit_c, extract, model

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def commands():
    return extract.extract_tree(PACKAGE)


class TestImageAnnotations:
    def test_a_two_dimensional_upload(self, commands):
        """``glTexImage2D(target, level, internalformat, width, height,
        border, format, type, pixels)``."""
        command = commands[('GL', 'glTexImage2D')]
        pixels = command.parameters[-1]
        assert isinstance(pixels.size, model.ImageSize)
        names = [p.name for p in command.parameters]
        assert names[pixels.size.format_argument] == 'format'
        assert names[pixels.size.type_argument] == 'type'
        assert [names[i] for i in pixels.size.dimensions] == ['width', 'height']

    def test_a_three_dimensional_upload(self, commands):
        command = commands[('GL', 'glTexImage3D')]
        pixels = command.parameters[-1]
        names = [p.name for p in command.parameters]
        assert [names[i] for i in pixels.size.dimensions] == [
            'width',
            'height',
            'depth',
        ]

    def test_a_one_dimensional_upload(self, commands):
        command = commands[('GL', 'glTexImage1D')]
        pixels = command.parameters[-1]
        names = [p.name for p in command.parameters]
        assert [names[i] for i in pixels.size.dimensions] == ['width']

    def test_a_read_is_an_output(self, commands):
        """``glReadPixels`` writes into the caller's buffer, or allocates."""
        command = commands[('GL', 'glReadPixels')]
        pixels = command.parameters[-1]
        assert pixels.direction == model.OUT
        assert isinstance(pixels.size, model.ImageSize)

    def test_an_upload_is_an_input(self, commands):
        assert commands[('GL', 'glTexImage2D')].parameters[-1].direction == model.IN

    def test_the_family_is_recognised_across_apis(self, commands):
        for api in ('GL', 'GLES2'):
            command = commands.get((api, 'glTexImage2D'))
            if command is None:
                continue
            assert isinstance(command.parameters[-1].size, model.ImageSize)


class TestImageEmission:
    def test_an_upload_is_emitted(self, commands):
        assert emit_c.is_emittable(commands[('GL', 'glTexImage3D')])

    def test_the_bases_of_typed_variants_are_emitted_too(self, commands):
        """images.py derives glDrawPixelsub(format, image) from glDrawPixels.

        It rebinds each customisation rather than applying it in place, so the
        base can be an entry point of ours while the variant still comes out
        with its own signature.
        """
        for name in ('glTexImage2D', 'glReadPixels', 'glDrawPixels'):
            assert emit_c.is_emittable(commands[('GL', name)]), name

    def test_an_upload_names_its_format_type_and_dimensions(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glTexImage3D')])
        assert (
            'PYGL_IMAGE_IN(9, pixels, format, type, 3, width, height, depth);'
            in text
        )

    def test_a_read_allocates_or_accepts(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glGetTexImage')])
        assert 'PYGL_IMAGE_OUT' in text
        assert 'pygl_image_value' in text


class TestCoverage:
    def test_the_family_is_described_rather_than_handed_to_python(self, commands):
        """What is left is the compressed uploads that carry their own size and
        the queries whose extent comes from the object, not from arguments."""
        remaining = [
            '%s.%s' % key
            for key, command in commands.items()
            if emit_c.exclusion_reason(command).startswith('hand-written family: image')
        ]
        assert len(remaining) < 40, remaining[:20]
