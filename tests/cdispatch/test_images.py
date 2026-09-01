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
        assert emit_c.is_emittable(commands[('GL', 'glTexImage2D')])

    def test_a_read_is_emitted(self, commands):
        assert emit_c.is_emittable(commands[('GL', 'glReadPixels')])

    def test_an_upload_names_its_format_type_and_dimensions(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glTexImage2D')])
        assert 'PYGL_IMAGE_IN(8, pixels, format, type, 2, width, height, 0);' in text

    def test_a_read_allocates_or_accepts(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glReadPixels')])
        assert 'PYGL_IMAGE_OUT(6, pixels, format, type, 2, width, height, 0);' in text
        assert 'pygl_image_value' in text

    def test_a_one_dimensional_upload_pads_its_dimensions(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glTexImage1D')])
        assert 'PYGL_IMAGE_IN(7, pixels, format, type, 1, width, 0, 0);' in text


class TestCoverage:
    def test_the_family_is_no_longer_excluded(self, commands):
        remaining = [
            key
            for key, command in commands.items()
            if emit_c.exclusion_reason(command).startswith('image')
        ]
        assert remaining == [], remaining[:20]
