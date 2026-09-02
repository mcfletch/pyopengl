"""A synthesised module has to behave like the file it stands in for.

The finder answers for module names whose ``.py`` files the tree still ships,
which is what makes the two comparable: anywhere the synthesised module and the
file disagree, a program that upgrades sees a change it did not ask for.
"""

import ast
import ctypes
import importlib
import os
import sys
import types

import pytest

from OpenGL import arrays
from OpenGL._dispatch import finder


class TestReExportsFollowStarImport:
    """``from ... import *`` takes ``__all__`` where the source defines one."""

    @pytest.fixture
    def source(self, monkeypatch):
        module = types.ModuleType('pygl_fake_source')
        module.__all__ = ['exported']
        module.exported = 'yes'
        module.public_but_not_exported = 'no'
        module._private = 'no'
        monkeypatch.setitem(sys.modules, 'pygl_fake_source', module)
        return module

    def synthesise(self, reexports, extension_name='GL_VERSION_GL_1_1'):
        loader = finder.RawModuleFinder.__new__(finder.RawModuleFinder)
        loader._extension = _FakeExtension(
            {'extension': extension_name, 'reexports': reexports,
             'constants': {}, 'commands': ()}
        )
        loader._entry_points = {}
        module = types.ModuleType('OpenGL.raw.GL.VERSION.GL_1_1')
        loader.exec_module(module)
        return module

    def test_a_source_with_all_contributes_only_what_it_names(self, source):
        module = self.synthesise(['pygl_fake_source'])
        assert module.exported == 'yes'
        assert not hasattr(module, 'public_but_not_exported')

    def test_a_source_without_all_contributes_every_public_name(self, source):
        del source.__all__
        module = self.synthesise(['pygl_fake_source'])
        assert module.public_but_not_exported == 'no'
        assert not hasattr(module, '_private')

    def test_an_all_naming_something_absent_is_an_import_error(self, source):
        source.__all__ = ['exported', 'never_defined']
        with pytest.raises(ImportError, match='never_defined'):
            self.synthesise(['pygl_fake_source'])


class TestTypeExpressionsAreReadNotExecuted:
    """The table is a data file, and a data file must not be able to run code."""

    @pytest.fixture
    def namespace(self):
        _cs = importlib.import_module('OpenGL.raw.GL._types')
        return {'ctypes': ctypes, 'arrays': arrays, '_cs': _cs}

    @pytest.mark.parametrize(
        'text,expected',
        [
            ('None', None),
            ('ctypes.c_void_p', ctypes.c_void_p),
        ],
    )
    def test_a_plain_expression_resolves(self, namespace, text, expected):
        assert finder._resolve_type(text, namespace) is expected

    def test_a_gl_typedef_resolves(self, namespace):
        assert finder._resolve_type('_cs.GLenum', namespace) is namespace['_cs'].GLenum

    def test_an_array_type_resolves(self, namespace):
        assert finder._resolve_type('arrays.GLfloatArray', namespace) is (
            arrays.GLfloatArray
        )

    def test_a_call_resolves(self, namespace):
        result = finder._resolve_type('ctypes.POINTER(_cs.GLchar)', namespace)
        assert result is ctypes.POINTER(namespace['_cs'].GLchar)

    @pytest.mark.parametrize(
        'text',
        [
            '__import__("os").system("true")',
            '(lambda: 1)()',
            'ctypes.c_int if 1 else None',
            '[ctypes.c_int]',
            'ctypes.CFUNCTYPE(restype=None)',
            '1 + 1',
        ],
    )
    def test_anything_that_is_not_a_type_expression_is_refused(
        self, namespace, text
    ):
        with pytest.raises(ValueError):
            finder._resolve_type(text, namespace)

    def test_an_unknown_name_is_refused_rather_than_looked_up(self, namespace):
        with pytest.raises(ValueError, match='unknown name'):
            finder._resolve_type('os.getcwd', namespace)

    def test_nothing_in_the_shipped_table_fails_to_resolve(self, namespace):
        """Every expression the generator wrote is one this evaluator reads."""
        from cdispatch import modules

        root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), 'OpenGL'
        )
        if not os.path.isdir(os.path.join(root, 'raw', 'GL')):
            pytest.skip('no raw tree to read declarations from')
        seen = 0
        for module in modules.read_modules(root, ['GL'])[:60]:
            for command in module.commands:
                for text in command.types:
                    parsed = ast.parse(text, mode='eval')
                    assert finder._evaluate(parsed.body, text, namespace) is not (
                        Ellipsis
                    )
                    seen += 1
        assert seen > 100


class TestTheFileAModuleStandsIn:
    def test_a_tree_without_the_files_states_no_file(self, monkeypatch):
        """After the files are dropped, no path is invented and none is stat'd."""
        monkeypatch.setattr(finder, '_shipped_root', None)
        import OpenGL

        monkeypatch.setattr(OpenGL, '__path__', ['/nonexistent/OpenGL'])
        assert finder._file_for('OpenGL.raw.GL.VERSION.GL_1_1') == ''

    def test_a_namespace_package_states_no_file(self, monkeypatch):
        """Several path entries mean no single directory to name."""
        monkeypatch.setattr(finder, '_shipped_root', None)
        import OpenGL

        monkeypatch.setattr(OpenGL, '__path__', ['/one', '/two'])
        assert finder._file_for('OpenGL.raw.GL.VERSION.GL_1_1') == ''

    def test_the_root_is_resolved_once(self, monkeypatch):
        """Not a stat of the raw directory per module imported."""
        monkeypatch.setattr(finder, '_shipped_root', None)
        calls = []
        real = os.path.isdir
        monkeypatch.setattr(
            os.path, 'isdir', lambda path: calls.append(path) or real(path)
        )
        for _ in range(5):
            finder._file_for('OpenGL.raw.GL.VERSION.GL_1_1')
        assert len(calls) == 1, calls


class _FakeExtension:
    def __init__(self, contents):
        self._contents = contents

    def module_names(self):
        return ()

    def module_contents(self, name):
        return self._contents
