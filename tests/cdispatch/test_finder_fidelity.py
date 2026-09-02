"""How the finder builds a module, checked at the seams a table cannot state.

Re-exports have to follow ``from ... import *`` exactly, including the
``__all__`` that two of the sources define; type expressions have to be read
rather than executed, because the table is a data file and a data file must not
be able to run code; and the path a module names has to cost nothing per
import.
"""

import ast
import ctypes
import importlib
import importlib.resources
import os
import sys
import types

import pytest

from OpenGL import _declarations, arrays
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


class TestTheTableAModuleNames:
    """``__file__`` names the table the definitions were read from.

    The full behaviour is in ``tests/test_raw_module_protocol.py``; what is
    here is the two things that are properties of the *finder* rather than of
    the module: that the answer costs nothing per import, and that a package
    which is not a directory on disk reports no file rather than a wrong one.
    """

    def test_the_path_is_resolved_once_per_api(self, monkeypatch):
        """find_spec asks for every generated module imported."""
        _declarations._table_paths.clear()
        calls = []
        real = os.path.exists
        monkeypatch.setattr(
            os.path, 'exists', lambda path: calls.append(path) or real(path)
        )
        for _ in range(5):
            _declarations.table_path('GL')
        assert len(calls) == 1, calls

    def test_a_package_that_is_not_a_directory_names_no_file(self, monkeypatch):
        """Inside a zip there is no path, and absence is the honest answer."""

        class _NotAFile:
            """A resource that os.fspath cannot turn into a path."""

            def __truediv__(self, other):
                return self

        _declarations._table_paths.clear()
        monkeypatch.setattr(
            importlib.resources, 'files', lambda package: _NotAFile()
        )
        assert _declarations.table_path('GL') is None


class _FakeExtension:
    def __init__(self, contents):
        self._contents = contents

    def module_names(self):
        return ()

    def module_contents(self, name):
        return self._contents
