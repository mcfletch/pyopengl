"""The C type model the generator reads registry declarations into."""

import pytest

from cdispatch import ctypes_model as cm


@pytest.mark.parametrize(
    'declaration,base,pointers,const',
    [
        ('void', 'void', 0, False),
        ('GLenum', 'GLenum', 0, False),
        ('GLuint', 'GLuint', 0, False),
        ('const GLfloat *', 'GLfloat', 1, True),
        ('const GLfloat*', 'GLfloat', 1, True),
        ('GLfloat *', 'GLfloat', 1, False),
        ('void *', 'void', 1, False),
        ('const void *', 'void', 1, True),
        ('void **', 'void', 2, False),
        ('const GLchar *const*', 'GLchar', 2, True),
        ('const GLubyte *', 'GLubyte', 1, True),
        ('struct _cl_context *', 'struct _cl_context', 1, False),
    ],
)
def test_parses_declarations(declaration, base, pointers, const):
    parsed = cm.parse_type(declaration)
    assert parsed.base == base
    assert parsed.pointers == pointers
    assert parsed.const == const


def test_declaration_round_trips():
    """The parsed form renders back to a C declaration the compiler accepts."""
    for declaration in ('void', 'GLuint', 'const GLfloat *', 'void **'):
        assert cm.parse_type(declaration).declaration() == declaration


@pytest.mark.parametrize(
    'declaration,macro',
    [
        ('GLenum', 'GL_U'),
        ('GLuint', 'GL_U'),
        ('GLint', 'GL_I'),
        ('GLsizei', 'GL_I'),
        ('GLbitfield', 'GL_U'),
        ('GLboolean', 'GL_B'),
        ('GLfloat', 'GL_F'),
        ('GLclampf', 'GL_F'),
        ('GLdouble', 'GL_D'),
        ('GLbyte', 'GL_I'),
        ('GLubyte', 'GL_U'),
        ('GLshort', 'GL_I'),
        ('GLushort', 'GL_U'),
        ('GLint64', 'GL_I64'),
        ('GLuint64', 'GL_U64'),
        ('GLintptr', 'GL_IPTR'),
        ('GLsizeiptr', 'GL_IPTR'),
        ('GLsync', 'GL_OPAQUE'),
    ],
)
def test_scalar_converter_macros(declaration, macro):
    assert cm.scalar_macro(cm.parse_type(declaration)) == macro


@pytest.mark.parametrize(
    'base,format_code,itemsize',
    [
        ('GLfloat', 'f', 4),
        ('GLdouble', 'd', 8),
        ('GLint', 'i', 4),
        ('GLuint', 'I', 4),
        ('GLshort', 'h', 2),
        ('GLushort', 'H', 2),
        ('GLbyte', 'b', 1),
        ('GLubyte', 'B', 1),
        ('GLint64', 'q', 8),
        ('GLuint64', 'Q', 8),
    ],
)
def test_element_types_carry_a_buffer_format(base, format_code, itemsize):
    element = cm.element_type(base)
    assert element.buffer_format == format_code
    assert element.itemsize == itemsize


def test_unknown_element_type_has_no_buffer_format():
    """An element type with no ``struct`` code never matches the fast path.

    Calls for it take the Python handler chain, which is correct if
    unaccelerated, from the day the type appears in the registry.
    """
    element = cm.element_type('GLDEBUGPROC')
    assert element.buffer_format == ''


def test_void_is_not_a_scalar():
    assert not cm.is_scalar(cm.parse_type('void'))
    assert cm.is_scalar(cm.parse_type('GLuint'))
    assert not cm.is_scalar(cm.parse_type('const GLfloat *'))


@pytest.mark.parametrize(
    'declaration,c_type',
    [
        ('GLenum', 'unsigned int'),
        ('GLuint', 'unsigned int'),
        ('GLint', 'int'),
        ('GLsizei', 'int'),
        ('GLboolean', 'unsigned char'),
        ('GLfloat', 'float'),
        ('GLdouble', 'double'),
        ('GLint64', 'int64_t'),
        ('GLuint64', 'uint64_t'),
        ('GLintptr', 'intptr_t'),
        ('GLsizeiptr', 'ptrdiff_t'),
        ('GLsync', 'void *'),
        ('GLhandleARB', 'PyGL_GLhandleARB'),
        ('unsigned long', 'unsigned long'),
        ('const GLfloat *', 'void *'),
        ('void *', 'void *'),
        ('void', 'void'),
    ],
)
def test_abi_c_type(declaration, c_type):
    """The signature the generated stub casts the slot's address to."""
    assert cm.abi_c_type(cm.parse_type(declaration)) == c_type
