#! /usr/bin/env python3
"""Signatures read from the ``.pyi`` stubs beside the package.

An entry point is built from the declaration tables when it is first used, so
introspecting one gives the wrapper's shape rather than the call's, and its
``__annotations__`` are there only where ``OpenGL.TYPE_ANNOTATIONS`` is set.
The stubs carry the types either way -- one per module, generated from the
same tables -- so that is where the documentation reads them from.
"""

import os

from directdocs import stubs

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, 'stub_samples')


class TestReadingAStub:
    def test_a_signature_carries_its_annotations(self, tmp_path):
        (tmp_path / 'sample.pyi').write_text(
            'def glDrawArraysInstancedBaseInstance(mode: int, first: int,\n'
            '        count: int) -> None: ...\n',
            encoding='utf-8',
        )
        found = stubs.read_stub(str(tmp_path / 'sample.pyi'))
        assert found['glDrawArraysInstancedBaseInstance'] == (
            'glDrawArraysInstancedBaseInstance(mode: int, first: int, '
            'count: int) -> None'
        )

    def test_a_default_is_kept(self, tmp_path):
        (tmp_path / 'sample.pyi').write_text(
            'def glGenBuffers(n: int, buffers: UIntArray | None = None)'
            ' -> UIntArrayResult: ...\n',
            encoding='utf-8',
        )
        found = stubs.read_stub(str(tmp_path / 'sample.pyi'))
        assert found['glGenBuffers'] == (
            'glGenBuffers(n: int, buffers: UIntArray | None = None) '
            '-> UIntArrayResult'
        )

    def test_a_function_with_no_return_annotation_has_none_written(self, tmp_path):
        (tmp_path / 'sample.pyi').write_text(
            'def glFinish(): ...\n', encoding='utf-8'
        )
        assert stubs.read_stub(str(tmp_path / 'sample.pyi')) == {
            'glFinish': 'glFinish()'
        }

    def test_the_catch_all_is_not_a_function(self, tmp_path):
        """``__getattr__`` is how a stub says "and whatever else"."""
        (tmp_path / 'sample.pyi').write_text(
            'def __getattr__(name: str) -> Any: ...\n', encoding='utf-8'
        )
        assert stubs.read_stub(str(tmp_path / 'sample.pyi')) == {}

    def test_a_method_is_found_under_its_class(self, tmp_path):
        (tmp_path / 'sample.pyi').write_text(
            'class VBO:\n'
            '    def bind(self) -> None: ...\n'
            '    def set_array(self, data: AnyArray, size: int | None = None)'
            ' -> None: ...\n',
            encoding='utf-8',
        )
        found = stubs.read_stub(str(tmp_path / 'sample.pyi'))
        assert found['VBO.set_array'] == (
            'set_array(self, data: AnyArray, size: int | None = None) -> None'
        )

    def test_a_stub_that_is_not_there_is_no_signatures(self, tmp_path):
        assert stubs.read_stub(str(tmp_path / 'absent.pyi')) == {}

    def test_a_stub_that_does_not_parse_is_no_signatures(self, tmp_path):
        """A broken stub leaves the page as it was rather than failing the run."""
        (tmp_path / 'sample.pyi').write_text('def (: ...\n', encoding='utf-8')
        assert stubs.read_stub(str(tmp_path / 'sample.pyi')) == {}


class TestFindingTheStub:
    def test_it_sits_beside_the_module(self):
        path = stubs.stub_path('OpenGL.GL.ARB.base_instance')
        assert path is not None
        assert path.endswith(os.path.join('GL', 'ARB', 'base_instance.pyi'))
        assert os.path.isfile(path)

    def test_a_package_has_its_own(self):
        path = stubs.stub_path('OpenGL.GL')
        assert path is not None
        assert path.endswith(os.path.join('GL', '__init__.pyi'))

    def test_a_package_outside_the_roots_has_none(self):
        assert stubs.stub_path('os.path') is None


class TestWhatThePackageShips:
    def test_a_generated_extension_module_is_covered(self):
        found = stubs.signatures('OpenGL.GL.ARB.base_instance')
        assert found['glDrawArraysInstancedBaseInstance'].startswith(
            'glDrawArraysInstancedBaseInstance(mode: int,'
        )
        assert found['glDrawArraysInstancedBaseInstance'].endswith('-> None')

    def test_an_unstubbed_module_answers_empty(self):
        assert stubs.signatures('directdocs.stubs') == {}


class TestOverloads:
    def test_the_first_form_is_the_one_kept(self, tmp_path):
        """Fourteen entry points are `@overload` sets; one signature is shown."""
        (tmp_path / 'sample.pyi').write_text(
            'from typing import overload\n'
            '@overload\n'
            'def glDeleteTextures(n: int, textures: UIntArray) -> None: ...\n'
            '@overload\n'
            'def glDeleteTextures(textures: UIntArray) -> None: ...\n',
            encoding='utf-8',
        )
        found = stubs.read_stub(str(tmp_path / 'sample.pyi'))
        assert found['glDeleteTextures'] == (
            'glDeleteTextures(n: int, textures: UIntArray) -> None'
        )
