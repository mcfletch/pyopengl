"""The type stubs, generated from the same command record as the C.

The signature and the size annotations already say which parameter becomes the
return value and which arguments a caller must supply, so the stub is derivable
rather than written; that is what makes shipping stubs worth doing rather than
merely possible.
"""

from cdispatch import emit_pyi, model
from cdispatch.ctypes_model import parse_type


def command(name='glBindTexture', return_type='void', parameters=(), **kwargs):
    kwargs.setdefault('api', 'GL')
    return model.Command(
        name=name,
        return_type=parse_type(return_type),
        parameters=[
            model.Parameter(name=n, ctype=parse_type(t), **extra)
            for n, t, extra in parameters
        ],
        **kwargs,
    )


class TestSignatures:
    def test_a_pass_through_call(self):
        text = emit_pyi.emit_signature(
            command(parameters=[('target', 'GLenum', {}), ('texture', 'GLuint', {})])
        )
        assert text == 'def glBindTexture(target: int, texture: int) -> None: ...'

    def test_a_float_argument(self):
        text = emit_pyi.emit_signature(
            command(
                name='glClearDepth',
                parameters=[('depth', 'GLdouble', {})],
            )
        )
        assert 'depth: float' in text

    def test_a_boolean_argument(self):
        text = emit_pyi.emit_signature(
            command(
                name='glDepthMask',
                parameters=[('flag', 'GLboolean', {})],
            )
        )
        assert 'flag: bool' in text

    def test_an_input_array(self):
        text = emit_pyi.emit_signature(
            command(
                name='glUniform1fv',
                parameters=[
                    ('location', 'GLint', {}),
                    ('count', 'GLsizei', {}),
                    ('value', 'const GLfloat *', {}),
                ],
            )
        )
        assert 'value: FloatArray' in text

    def test_an_output_array_becomes_the_return(self):
        """``glGenTextures(n)`` returns an array; the size spec already said so."""
        text = emit_pyi.emit_signature(
            command(
                name='glGenTextures',
                parameters=[
                    ('n', 'GLsizei', {}),
                    (
                        'textures',
                        'GLuint *',
                        {'direction': model.OUT, 'size': model.FromArg(argument=0)},
                    ),
                ],
            )
        )
        assert (
            text
            == 'def glGenTextures(n: int, textures: UIntArray | None = None)'
            ' -> UIntArrayResult: ...'
        )

    def test_several_outputs_return_a_tuple(self):
        text = emit_pyi.emit_signature(
            command(
                name='glGetShaderPrecisionFormat',
                parameters=[
                    ('shadertype', 'GLenum', {}),
                    (
                        'precision',
                        'GLint *',
                        {'direction': model.OUT, 'size': model.Fixed(1)},
                    ),
                    (
                        'range',
                        'GLint *',
                        {
                            'direction': model.OUT,
                            'size': model.Fixed(2),
                            'output_order': 1,
                        },
                    ),
                ],
            )
        )
        assert text.endswith('-> tuple[IntArrayResult, IntArrayResult]: ...')

    def test_a_scalar_return(self):
        text = emit_pyi.emit_signature(
            command(
                name='glIsTexture',
                return_type='GLboolean',
                parameters=[('texture', 'GLuint', {})],
            )
        )
        assert text.endswith('-> int: ...')

    def test_a_string_return(self):
        text = emit_pyi.emit_signature(
            command(
                name='glGetString',
                return_type='const GLubyte *',
                parameters=[('name', 'GLenum', {})],
            )
        )
        assert text.endswith('-> bytes: ...')

    def test_a_reserved_python_word_is_not_used_as_a_parameter(self):
        """``lambda`` and friends appear as registry parameter names."""
        text = emit_pyi.emit_signature(
            command(
                name='glTexParameterf',
                parameters=[('lambda', 'GLfloat', {})],
            )
        )
        assert 'lambda:' not in text


class TestModule:
    def test_a_stub_module_carries_its_docstrings(self):
        text = emit_pyi.emit_module(
            'GL',
            [command(parameters=[('target', 'GLenum', {}), ('texture', 'GLuint', {})])],
        )
        assert '"""glBindTexture(target, texture) -> None"""' in text

    def test_the_array_aliases_are_declared(self):
        text = emit_pyi.emit_module('GL', [])
        assert 'FloatArray' in text
        assert 'from __future__ import annotations' in text


class TestValidPython:
    """A stub file that does not parse is worse than no stub file."""

    def test_a_module_parses(self):
        import ast

        text = emit_pyi.emit_module(
            'GL',
            [
                command(
                    parameters=[('target', 'GLenum', {}), ('texture', 'GLuint', {})]
                ),
                command(
                    name='glGenTextures',
                    parameters=[
                        ('n', 'GLsizei', {}),
                        (
                            'textures',
                            'GLuint *',
                            {
                                'direction': model.OUT,
                                'size': model.FromArg(argument=0),
                            },
                        ),
                    ],
                ),
                command(name='glShaderSource', api='GL'),
            ],
        )
        ast.parse(text)

    def test_the_whole_generated_tree_parses(self):
        import ast
        import os

        from cdispatch import extract

        here = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        commands = extract.extract_tree(os.path.join(here, 'OpenGL'))
        for api in ('GL', 'GLES2', 'EGL'):
            selected = [c for key, c in commands.items() if key[0] == api]
            ast.parse(emit_pyi.emit_module(api, selected))


class TestConstants:
    """A stub that declares only the functions would reject GL_TEXTURE_2D.

    The enums are most of what a caller writes, so a stub without them makes a
    type checker reject correct code -- worse than shipping no stub at all.
    """

    def test_constants_are_declared(self):
        text = emit_pyi.emit_module(
            'GL', [], constants=['GL_TEXTURE_2D', 'GL_TRIANGLES']
        )
        assert 'GL_TEXTURE_2D: int' in text
        assert 'GL_TRIANGLES: int' in text

    def test_the_shipped_tree_declares_its_constants(self):
        import os

        from cdispatch import extract

        here = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        constants = extract.extract_constants(os.path.join(here, 'OpenGL'))
        assert 'GL_TEXTURE_2D' in constants['GL']
        assert 'GL_ARRAY_BUFFER' in constants['GL']
        assert len(constants['GL']) > 5000
