"""What the generated ``OpenGL/raw`` modules are made of.

Reading them into data is what lets the C table stand in for the files, so
what the reader gets out of a declaration is the whole question: get the
signature wrong and a client that demotes to the ctypes binding gets a wrong
one silently.
"""

import os

import pytest

from cdispatch import extract, modules

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')


@pytest.fixture(scope='module')
def raw_modules():
    return modules.read_modules(PACKAGE, extract.APIS)


class TestReading:
    def test_the_whole_tree_is_described(self, raw_modules):
        assert len(raw_modules) > 1200

    def test_a_module_carries_its_extension_name(self, raw_modules):
        module = _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_1')
        assert module.extension == 'GL_VERSION_GL_1_1'

    def test_a_module_carries_its_constants(self, raw_modules):
        module = _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_1')
        assert module.constants['GL_PROXY_TEXTURE_2D'] == 0x8064

    def test_a_constant_stays_where_it_was_defined(self, raw_modules):
        """GL_TEXTURE_2D is GL_1_0's; GL_1_1 gets it by re-export."""
        module = _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_1')
        assert 'GL_TEXTURE_2D' not in module.constants
        assert _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_0').constants[
            'GL_TEXTURE_2D'
        ] == 0x0DE1

    def test_a_module_carries_what_it_re_exports(self, raw_modules):
        module = _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_1')
        assert 'OpenGL.raw.GL.VERSION.GL_1_0' in module.reexports

    def test_what_a_table_cannot_describe_keeps_its_file(self, raw_modules):
        """A module with a class or a conditional in it is not data."""
        described = {module.name for module in raw_modules}
        assert 'OpenGL.raw.GLU.constants' not in described


class TestConstantValues:
    """A constant's value has to survive the round trip through C.

    Most are small positive enums, but the range runs from -6
    (``GL_SKIP_COMPONENTS4_NV``) to 2**64-1 (``GL_TIMEOUT_IGNORED``), which no
    single C integer type covers.
    """

    def test_a_negative_constant_stays_negative(self, raw_modules):
        module = _module(raw_modules, 'OpenGL.raw.GL.NV.transform_feedback')
        assert module.constants['GL_SKIP_COMPONENTS4_NV'] == -3
        assert module.constants['GL_NEXT_BUFFER_NV'] == -2

    def test_a_negative_constant_is_emitted_as_negative(self, raw_modules):
        text = modules.emit_modules(raw_modules)
        assert '{"GL_NEXT_BUFFER_NV", (unsigned long long)(-2LL), 1}' in text

    def test_the_largest_constant_survives(self, raw_modules):
        module = _module(raw_modules, 'OpenGL.raw.GL.VERSION.GL_3_2')
        assert module.constants['GL_TIMEOUT_IGNORED'] == 0xFFFFFFFFFFFFFFFF

    def test_the_largest_constant_is_emitted_unsigned(self, raw_modules):
        text = modules.emit_modules(raw_modules)
        assert '{"GL_TIMEOUT_IGNORED", 18446744073709551615ULL, 0}' in text


class TestEmission:
    def test_the_table_names_every_module(self, raw_modules):
        text = modules.emit_modules(raw_modules)
        assert 'const PyGLModule pygl_modules[]' in text
        assert '"OpenGL.raw.GL.VERSION.GL_1_1"' in text

    def test_a_declaration_row_carries_its_signature(self, raw_modules):
        text = modules.emit_modules(raw_modules)
        assert '"glTexImage3D", "target,level,internalformat' in text

    def test_the_count_matches(self, raw_modules):
        text = modules.emit_modules(raw_modules)
        assert 'pygl_module_count = %d;' % (len(raw_modules),) in text


def _module(raw_modules, name):
    return [item for item in raw_modules if item.name == name][0]



class TestDeclarations:
    """A module's entry points carry the signature their declaration stated.

    ``@_p.types(None, _cs.GLenum, ...)`` is what recorded the ctypes binding a
    client demotes to, and with no file to run there is nothing else to say it.
    """

    def test_a_command_carries_its_argument_names(self, raw_modules):
        command = _command(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_2', 'glTexImage3D')
        assert command.argument_names[:3] == ('target', 'level', 'internalformat')

    def test_a_command_carries_its_types_result_first(self, raw_modules):
        command = _command(raw_modules, 'OpenGL.raw.GL.VERSION.GL_1_2', 'glTexImage3D')
        assert command.types[0] == 'None'
        assert command.types[1] == '_cs.GLenum'
        assert len(command.types) == len(command.argument_names) + 1

    def test_a_nested_ctypes_expression_survives(self, raw_modules):
        """``ctypes.POINTER(ctypes.POINTER(_cs.GLchar))`` is a call, not a name."""
        command = _command(raw_modules, 'OpenGL.raw.GL.VERSION.GL_2_0', 'glShaderSource')
        assert 'ctypes.POINTER(ctypes.POINTER(_cs.GLchar))' in command.types

    def test_an_array_type_survives(self, raw_modules):
        command = _command(raw_modules, 'OpenGL.raw.GL.VERSION.GL_2_0', 'glShaderSource')
        assert 'arrays.GLintArray' in command.types

    def test_the_types_name_only_what_can_be_resolved(self, raw_modules):
        """Whatever a declaration reaches for, the finder has to resolve, so
        the reader accepts only the three namespaces it can offer."""
        from cdispatch import modules

        for module in raw_modules:
            for command in module.commands:
                for text in command.types:
                    if text == 'None':
                        continue
                    root = text.split('.', 1)[0].split('(', 1)[0]
                    assert root in modules.TYPE_NAMESPACES, (command.name, text)


def _command(raw_modules, module_name, command_name):
    module = [item for item in raw_modules if item.name == module_name][0]
    return [item for item in module.commands if item.name == command_name][0]
