#! /usr/bin/env python3
"""How a declaration's type expressions are read.

The text arrives from a data file -- the marshalled tables, or the strings the C
extension carries in ``.rodata`` -- and a data file that can run code is a
different kind of file.  So the expressions are *read* rather than executed:
the vocabulary a declaration is written in is attribute lookups on three names
and calls to a handful of ctypes constructors, and nothing else is accepted.

One reader serves both routes.  The C route and the table route describe the
same declarations, and two readers with two answers to "may this text run?" is
one reader too many.
"""

import ctypes

import pytest

from OpenGL import _declarations, arrays


@pytest.fixture
def namespace():
    return {
        'ctypes': ctypes,
        'arrays': arrays,
        '_cs': __import__('OpenGL.raw.GL._types', fromlist=['_types']),
    }


class TestTheVocabularyADeclarationIsWrittenIn:
    def test_none(self, namespace):
        assert _declarations.resolve_type('None', namespace) is None

    def test_an_attribute(self, namespace):
        assert _declarations.resolve_type('_cs.GLenum', namespace) is ctypes.c_uint

    def test_a_name(self, namespace):
        assert _declarations.resolve_type('ctypes', namespace) is ctypes

    def test_an_array_type(self, namespace):
        assert _declarations.resolve_type(
            'arrays.GLfloatArray', namespace
        ) is arrays.GLfloatArray

    def test_a_pointer(self, namespace):
        pointer = _declarations.resolve_type('ctypes.POINTER(_cs.GLchar)', namespace)
        assert pointer is ctypes.POINTER(ctypes.c_char)


class TestWhatIsRefused:
    """A *call* is the thing that can make a data file run code, so calls are
    held to the handful of constructors a declared type is built with.  A bare
    attribute lookup reaches a value and runs nothing, so the vocabulary of
    names -- every ``_cs.GL*``, every ``arrays.*Array``, every ``ctypes.c_*`` --
    is not enumerated: an expression that names something that is not a type
    fails where the type is used, which is a wrong declaration rather than a
    way in."""

    @pytest.mark.parametrize(
        'text',
        [
            pytest.param('ctypes.CDLL("libc.so.6")', id='loads-a-library'),
            pytest.param('ctypes.memmove(0, 0, 0)', id='calls-something-else'),
            pytest.param('arrays.GLfloatArray.zeros(1)', id='calls-a-method'),
            pytest.param('__import__("os").system("true")', id='imports'),
            pytest.param('_cs.GLenum.__class__.__bases__', id='dunder'),
            pytest.param('1 + 1', id='arithmetic'),
            pytest.param('[ctypes]', id='a-list'),
            pytest.param('ctypes.POINTER(x=1)', id='keywords'),
            pytest.param('not a type expression', id='not-an-expression'),
        ],
    )
    def test_it_is_not_a_type_expression(self, namespace, text):
        with pytest.raises(ValueError):
            _declarations.resolve_type(text, namespace)

    def test_refusing_a_call_names_what_it_refused(self, namespace):
        with pytest.raises(ValueError) as caught:
            _declarations.resolve_type('ctypes.CDLL("libc.so.6")', namespace)
        assert 'CDLL' in str(caught.value)


class TestOneReaderServesBothRoutes:
    def test_the_finder_uses_the_same_declaration_class(self):
        from OpenGL._dispatch import finder

        assert finder.Declaration is _declarations.Declaration

    def test_the_finder_uses_the_same_type_reader(self):
        from OpenGL._dispatch import finder

        assert finder.resolve_type is _declarations.resolve_type


class TestADeclarationBuildsItsBinding:
    def test_the_binding_carries_the_declared_signature(self):
        declaration = _declarations.Declaration(
            'GL', 'glClear', 'GL_VERSION_GL_1_1',
            'OpenGL.raw.GL.VERSION.GL_1_1', 'mask', 'None,_cs.GLbitfield',
        )
        binding = declaration()
        assert binding.__name__ == 'glClear'
        assert binding.argNames == ('mask',)
        assert tuple(binding.argtypes) == (ctypes.c_uint,)


class TestEveryExpressionTheGeneratorWrote:
    """The vocabulary is a claim about what the generator emits, so it has to
    be checked against what the generator emitted.  A rule tightened without
    this sweep refuses a real declaration and the refusal shows up only when
    something demotes that one entry point."""

    def test_nothing_in_the_shipped_tree_is_refused(self):
        import importlib
        import os
        import sys

        import paths

        root = paths.ROOT
        sys.path.insert(0, paths.SRC)
        try:
            from cdispatch import modules
        except ImportError:  # pragma: no cover - a wheel install has no src/
            pytest.skip('the generator is not on the path')
        finally:
            sys.path.pop(0)
        package = os.path.join(root, 'OpenGL')
        if not os.path.isdir(os.path.join(package, 'raw', 'GL')):
            pytest.skip('no raw tree to read declarations from')

        seen, refused = 0, []
        for api in ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'EGL', 'GLX', 'WGL'):
            try:
                types = importlib.import_module('OpenGL.raw.%s._types' % (api,))
            except ImportError:  # pragma: no cover - depends on the platform
                continue
            space = {'ctypes': ctypes, 'arrays': arrays, '_cs': types}
            for module in modules.read_modules(package, [api]):
                for command in module.commands:
                    for text in command.types:
                        seen += 1
                        try:
                            _declarations.resolve_type(text, space)
                        except ValueError as error:
                            refused.append((api, text, str(error)))
                        except AttributeError:
                            # A name this API's _types does not carry: a wrong
                            # declaration rather than a refusal, and the same
                            # answer any reader would give.
                            pass
        assert seen > 20000, seen
        assert refused == [], refused[:5]

    def test_a_leading_underscore_is_not_a_dunder(self):
        """GLX declares ``__GLXextFuncPtr``.  The guard is against reaching
        Python's own machinery, which is named at both ends."""
        import importlib

        space = {
            'ctypes': ctypes,
            'arrays': arrays,
            '_cs': importlib.import_module('OpenGL.raw.GLX._types'),
        }
        assert _declarations.resolve_type('_cs.__GLXextFuncPtr', space) is not None
