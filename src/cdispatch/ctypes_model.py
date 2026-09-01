"""The C type vocabulary the registry declares parameters and returns in.

A registry declaration is a string such as ``const  GLfloat *``.  :func:`parse_type`
turns it into a :class:`CType`, and the tables below say what each base type
means to the generator: which converter macro reads it from a Python argument,
and — where it can be an array element — which ``struct`` format code a buffer
must export for the fast path to take it.

The element table is the extension point named in the arrays section of the
plan: a base type with no ``struct`` code gets an empty ``buffer_format``,
which never matches, so every call for it takes the Python handler chain.
"""

import re
from dataclasses import dataclass, field

__all__ = [
    'CType',
    'ElementType',
    'parse_type',
    'scalar_macro',
    'element_type',
    'is_scalar',
    'is_void',
]

_WHITESPACE = re.compile(r'\s+')


@dataclass(frozen=True)
class CType:
    """A parsed C declaration: a base type, a pointer depth and constness."""

    base: str
    pointers: int = 0
    const: bool = False

    def declaration(self):
        """Render back to a C declaration a compiler accepts."""
        parts = []
        if self.const:
            parts.append('const')
        parts.append(self.base)
        if self.pointers:
            return '%s %s' % (' '.join(parts), '*' * self.pointers)
        return ' '.join(parts)

    def element(self):
        """The type of what this points at, for a pointer type."""
        if not self.pointers:
            raise ValueError('%r is not a pointer' % (self.declaration(),))
        return CType(self.base, self.pointers - 1, self.const)


def parse_type(declaration):
    """Parse a registry type declaration into a :class:`CType`.

    Handles the forms the registry actually produces, including the doubled
    space in ``const  GLfloat *``, a trailing space on ``void ``, ``struct``
    tags, and a second ``const`` between the stars in ``const GLchar *const*``.
    """
    text = _WHITESPACE.sub(' ', declaration).strip()
    pointers = text.count('*')
    text = text.replace('*', ' ')
    words = text.split()
    const = 'const' in words
    words = [word for word in words if word != 'const']
    if words[:1] == ['struct']:
        base = 'struct %s' % (' '.join(words[1:]),)
    else:
        base = ' '.join(words)
    return CType(base or 'void', pointers, const)


#: Registry base type -> the macro that converts a Python argument to it.
#: ``GL_OPAQUE`` covers the typedef'd pointer handles (``GLsync`` and the
#: platform window-system handles), which arrive as integers or as the opaque
#: pointer objects ``OpenGL/_opaque.py`` builds.
_SCALAR_MACROS = {
    # unsigned integers
    'GLenum': 'GL_U',
    'GLuint': 'GL_U',
    'GLbitfield': 'GL_U',
    'GLubyte': 'GL_U',
    'GLushort': 'GL_U',
    'GLhalfNV': 'GL_U',
    'GLhandleARB': 'GL_HANDLE',
    'unsigned int': 'GL_U',
    'unsigned long': 'GL_U64',
    'UINT': 'GL_U',
    'DWORD': 'GL_U',
    'USHORT': 'GL_U',
    'COLORREF': 'GL_U',
    # signed integers
    'GLint': 'GL_I',
    'GLsizei': 'GL_I',
    'GLbyte': 'GL_I',
    'GLshort': 'GL_I',
    'GLfixed': 'GL_I',
    'GLclampx': 'GL_I',
    'int': 'GL_I',
    'INT': 'GL_I',
    'INT32': 'GL_I',
    'int32_t': 'GL_I',
    'BOOL': 'GL_I',
    'Bool': 'GL_I',
    'Status': 'GL_I',
    'char': 'GL_I',
    # booleans
    'GLboolean': 'GL_B',
    # floating point
    'GLfloat': 'GL_F',
    'GLclampf': 'GL_F',
    'float': 'GL_F',
    'FLOAT': 'GL_F',
    'GLdouble': 'GL_D',
    'GLclampd': 'GL_D',
    'double': 'GL_D',
    # 64-bit
    'GLint64': 'GL_I64',
    'GLint64EXT': 'GL_I64',
    'int64_t': 'GL_I64',
    'INT64': 'GL_I64',
    'GLuint64': 'GL_U64',
    'GLuint64EXT': 'GL_U64',
    # pointer-sized integers
    'GLintptr': 'GL_IPTR',
    'GLsizeiptr': 'GL_IPTR',
    'GLintptrARB': 'GL_IPTR',
    'GLsizeiptrARB': 'GL_IPTR',
    'GLvdpauSurfaceNV': 'GL_IPTR',
    'GLchar': 'GL_I',
    'GLcharARB': 'GL_I',
    # ``_types.py`` spells the plain C types as their ctypes names, so the raw
    # modules declare them that way and the extractor sees them so.
    'c_int': 'GL_I',
    'c_uint': 'GL_U',
    'c_ulong': 'GL_U64',
    'c_short': 'GL_I',
    'c_ushort': 'GL_U',
    'c_float': 'GL_F',
    'c_double': 'GL_D',
    # EGL.  The registry for these is not vendored, so the vocabulary comes
    # from the shipped OpenGL/raw/EGL/_types.py rather than from an XML file.
    'EGLint': 'GL_I',
    'EGLBoolean': 'GL_U',
    'EGLenum': 'GL_U',
    'EGLNativeFileDescriptorKHR': 'GL_I',
    'EGLTime': 'GL_U64',
    'EGLTimeKHR': 'GL_U64',
    'EGLTimeNV': 'GL_U64',
    'EGLuint64NV': 'GL_U64',
    'EGLuint64KHR': 'GL_U64',
    'EGLAttrib': 'GL_IPTR',
    'EGLAttribKHR': 'GL_IPTR',
    'EGLsizeiANDROID': 'GL_IPTR',
}

#: Typedef'd pointers.  Declared with no ``*`` in the registry but pointer-sized
#: and opaque to the caller.
_OPAQUE = frozenset(
    [
        'GLsync',
        'GLeglImageOES',
        'GLeglClientBufferEXT',
        'GLXContext',
        'GLXDrawable',
        'GLXPixmap',
        'GLXWindow',
        'GLXPbuffer',
        'GLXPbufferSGIX',
        'GLXFBConfig',
        'GLXFBConfigSGIX',
        'GLXContextID',
        'GLXVideoSourceSGIX',
        'GLXVideoDeviceNV',
        'GLXVideoCaptureDeviceNV',
        'Window',
        'Pixmap',
        'Font',
        'Colormap',
        'HDC',
        'HGLRC',
        'HANDLE',
        'HPBUFFERARB',
        'HPBUFFEREXT',
        'HPVIDEODEV',
        'HGPUNV',
        'HVIDEOINPUTDEVICENV',
        'HVIDEOOUTPUTDEVICENV',
        'HENHMETAFILE',
        'PROC',
        'LPVOID',
        'VOID',
        'LPCSTR',
        'VLServer',
        'VLPath',
        'VLNode',
        'DMbuffer',
        '__GLXextFuncPtr',
        'GLVULKANPROCNV',
        'GLDEBUGPROC',
        'GLDEBUGPROCARB',
        'GLDEBUGPROCKHR',
        'GLDEBUGPROCAMD',
        # EGL's opaque handles are all pointer-sized.
        'EGLDisplay',
        'EGLSurface',
        'EGLContext',
        'EGLConfig',
        'EGLClientBuffer',
        'EGLDeviceEXT',
        'EGLImage',
        'EGLImageKHR',
        'EGLStreamKHR',
        'EGLSync',
        'EGLSyncKHR',
        'EGLSyncNV',
        'EGLOutputLayerEXT',
        'EGLOutputPortEXT',
        'EGLObjectKHR',
        'EGLLabelKHR',
        'EGLNativeDisplayType',
        'EGLNativeWindowType',
        'EGLNativePixmapType',
        'EGLDEBUGPROCKHR',
        'EGLGetBlobFuncANDROID',
        'EGLSetBlobFuncANDROID',
        '__eglMustCastToProperFunctionPointerType',
        # Windows structure pointers, opaque to the binding.
        'LPGLYPHMETRICSFLOAT',
        'PGPU_DEVICE',
    ]
)


@dataclass(frozen=True)
class ElementType:
    """What an array of this base type looks like to the buffer protocol.

    ``buffer_format`` is the canonical ``struct`` code.  ``accepted_formats``
    is every code an exporter may legitimately use for the same machine type —
    numpy writes ``l`` rather than ``q`` for a 64-bit integer on LP64
    platforms, and both are the same eight bytes.  An empty ``buffer_format``
    means no buffer ever matches, so the parameter always takes the Python
    handler chain.
    """

    base: str
    buffer_format: str = ''
    itemsize: int = 0
    array_class: str = ''
    accepted_formats: tuple = field(default_factory=tuple)

    def matches(self):
        """The format codes the C fast path accepts for this element type."""
        return self.accepted_formats or (
            (self.buffer_format,) if self.buffer_format else ()
        )


def _element(base, code, size, array_class, extra=()):
    return ElementType(base, code, size, array_class, (code,) + tuple(extra))


#: Registry base type -> its array element description.  ``array_class`` names
#: the ``OpenGL.arrays`` class the fall-through path hands the argument to, so
#: a mismatch converts exactly as it does today.
_ELEMENTS = {
    'GLfloat': _element('GLfloat', 'f', 4, 'GLfloatArray'),
    'GLclampf': _element('GLclampf', 'f', 4, 'GLclampfArray'),
    'float': _element('float', 'f', 4, 'GLfloatArray'),
    'GLdouble': _element('GLdouble', 'd', 8, 'GLdoubleArray'),
    'GLclampd': _element('GLclampd', 'd', 8, 'GLdoubleArray'),
    'double': _element('double', 'd', 8, 'GLdoubleArray'),
    'GLint': _element('GLint', 'i', 4, 'GLintArray', ('l',)),
    'GLsizei': _element('GLsizei', 'i', 4, 'GLsizeiArray', ('l',)),
    'GLfixed': _element('GLfixed', 'i', 4, 'GLfixedArray', ('l',)),
    'GLclampx': _element('GLclampx', 'i', 4, 'GLfixedArray', ('l',)),
    'int': _element('int', 'i', 4, 'GLintArray', ('l',)),
    'GLuint': _element('GLuint', 'I', 4, 'GLuintArray', ('L',)),
    'GLenum': _element('GLenum', 'I', 4, 'GLuintArray', ('L',)),
    'GLbitfield': _element('GLbitfield', 'I', 4, 'GLuintArray', ('L',)),
    'unsigned int': _element('unsigned int', 'I', 4, 'GLuintArray', ('L',)),
    'GLhandleARB': _element('GLhandleARB', 'I', 4, 'GLuintArray', ('L',)),
    'c_int': _element('c_int', 'i', 4, 'GLintArray', ('l',)),
    'c_uint': _element('c_uint', 'I', 4, 'GLuintArray', ('L',)),
    'EGLint': _element('EGLint', 'i', 4, 'GLintArray', ('l',)),
    'EGLenum': _element('EGLenum', 'I', 4, 'GLuintArray', ('L',)),
    'EGLAttrib': _element('EGLAttrib', 'q', 8, 'EGLAttribArray', ('l', 'n')),
    'GLshort': _element('GLshort', 'h', 2, 'GLshortArray'),
    'GLushort': _element('GLushort', 'H', 2, 'GLushortArray'),
    'GLbyte': _element('GLbyte', 'b', 1, 'GLbyteArray'),
    'char': _element('char', 'b', 1, 'GLbyteArray', ('c',)),
    'GLubyte': _element('GLubyte', 'B', 1, 'GLubyteArray', ('c',)),
    'GLboolean': _element('GLboolean', 'B', 1, 'GLbooleanArray', ('?', 'c')),
    'GLchar': _element('GLchar', 'b', 1, 'GLcharArray', ('c', 'B')),
    'GLcharARB': _element('GLcharARB', 'b', 1, 'GLcharARBArray', ('c', 'B')),
    'GLint64': _element('GLint64', 'q', 8, 'GLint64Array', ('l',)),
    'GLint64EXT': _element('GLint64EXT', 'q', 8, 'GLint64Array', ('l',)),
    'int64_t': _element('int64_t', 'q', 8, 'GLint64Array', ('l',)),
    'GLuint64': _element('GLuint64', 'Q', 8, 'GLuint64Array', ('L',)),
    'GLuint64EXT': _element('GLuint64EXT', 'Q', 8, 'GLuint64Array', ('L',)),
    # GLhalfNV, GLintptr and GLsizeiptr arrays have no ArrayDatatype class:
    # PyOpenGL declares those parameters as ctypes pointers rather than array
    # types.  Leaving them out of this table means they take the generic path,
    # which is what they take today.
}


#: The C type each converter macro produces, used for the function-pointer cast
#: in the generated stub.
_MACRO_C_TYPE = {
    'GL_U': 'unsigned int',
    'GL_I': 'int',
    'GL_B': 'unsigned char',
    'GL_F': 'float',
    'GL_D': 'double',
    'GL_I64': 'int64_t',
    'GL_U64': 'uint64_t',
    'GL_IPTR': 'intptr_t',
    'GL_OPAQUE': 'void *',
    'GL_HANDLE': 'PyGL_GLhandleARB',
}

#: Base types whose ABI width differs from what the macro's class implies.
#: A narrow integer is passed as itself rather than promoted, so that the
#: prototype the stub casts to matches the one the driver was compiled with.
_EXACT_C_TYPE = {
    'GLbyte': 'signed char',
    'GLubyte': 'unsigned char',
    'char': 'char',
    'GLshort': 'short',
    'GLushort': 'unsigned short',
    'GLhalfNV': 'unsigned short',
    'USHORT': 'unsigned short',
    'unsigned long': 'unsigned long',
    'GLsizeiptr': 'ptrdiff_t',
    'GLsizeiptrARB': 'ptrdiff_t',
    'GLdouble': 'double',
    'GLclampd': 'double',
}


def abi_c_type(ctype):
    """The C type the generated stub declares for this parameter or return.

    Every pointer collapses to ``void *``: the stub hands the driver an address
    and the element type is the fast path's business, not the ABI's.
    """
    if ctype.pointers:
        return 'void *'
    if is_void(ctype):
        return 'void'
    if ctype.base in _EXACT_C_TYPE:
        return _EXACT_C_TYPE[ctype.base]
    macro = scalar_macro(ctype)
    if macro is None:
        # An unrecognised base is a typedef'd handle: pointer-sized and opaque.
        return 'void *'
    return _MACRO_C_TYPE[macro]


def scalar_macro(ctype):
    """The converter macro for a scalar parameter, or ``None`` if it is not one."""
    if ctype.pointers:
        return None
    if ctype.base in _SCALAR_MACROS:
        return _SCALAR_MACROS[ctype.base]
    if ctype.base in _OPAQUE:
        return 'GL_OPAQUE'
    return None


def element_type(base):
    """The array element description for a base type.

    A base type the table does not know gets an entry with no buffer format,
    so it never matches the fast path.
    """
    return _ELEMENTS.get(base) or ElementType(base)


def is_scalar(ctype):
    """True when the type is passed by value from a single Python argument."""
    return scalar_macro(ctype) is not None


def is_void(ctype):
    return ctype.base == 'void' and not ctype.pointers


def known_element_types():
    """Every element type the fast path can match, for the generated C table."""
    return [
        _ELEMENTS[base] for base in sorted(_ELEMENTS) if _ELEMENTS[base].buffer_format
    ]
