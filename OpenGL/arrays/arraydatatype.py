"""Array data-type implementations (abstraction points for GL array types"""
import ctypes
import OpenGL

assert OpenGL
from OpenGL.raw.GL import _types
from OpenGL import plugins
from OpenGL.arrays import formathandler, _arrayconstants as GL_1_1
from OpenGL import logs

_log = logs.getLog("OpenGL.arrays.arraydatatype")
from OpenGL._bytes import unicode
from OpenGL import acceleratesupport

ADT = None
if acceleratesupport.ACCELERATE_AVAILABLE:
    try:
        from OpenGL_accelerate.arraydatatype import ArrayDatatype as ADT
    except ImportError as err:
        _log.warning("Unable to load ArrayDatatype accelerator from OpenGL_accelerate")
if ADT is None:
    # Python-coded version
    class HandlerRegistry(dict):
        GENERIC_OUTPUT_PREFERENCES = ["numpy", "ctypesarrays"]

        def __init__(self, plugin_match):
            self.match = plugin_match
            self.output_handler = None
            self.preferredOutput = None
            self.all_output_handlers = []

        def __call__(self, value):
            """Lookup of handler for given value"""
            try:
                typ = value.__class__
            except AttributeError:
                typ = type(value)
            handler = self.get(typ)
            if not handler:
                if hasattr(typ, "__mro__"):
                    for base in typ.__mro__:
                        handler = self.get(base)
                        if not handler:
                            handler = self.match(base)
                            if handler:
                                handler = handler.load()
                                if handler:
                                    handler = handler()
                        if handler:
                            self[typ] = handler
                            if hasattr(handler, "registerEquivalent"):
                                handler.registerEquivalent(typ, base)
                            return handler
                print(self.keys())
                raise TypeError(
                    """No array-type handler for type %s.%s (value: %s) registered"""
                    % (typ.__module__, typ.__name__, repr(value)[:50])
                )
            return handler

        def handler_by_plugin_name(self, name):
            plugin = plugins.FormatHandler.by_name(name)
            if plugin:
                try:
                    return plugin.load()
                except ImportError:
                    return None
            else:
                raise RuntimeError("No handler of name %s found" % (name,))

        def get_output_handler(self):
            """Fast-path lookup for output handler object"""
            if self.output_handler is None:
                if self.preferredOutput is not None:
                    self.output_handler = self.handler_by_plugin_name(
                        self.preferredOutput
                    )
                if not self.output_handler:
                    for preferred in self.GENERIC_OUTPUT_PREFERENCES:
                        self.output_handler = self.handler_by_plugin_name(preferred)
                        if self.output_handler:
                            break
                if not self.output_handler:
                    raise RuntimeError(
                        """Unable to find any output handler at all (not even ctypes/numpy ones!)"""
                    )
            return self.output_handler

        def register(self, handler, types=None):
            """Register this class as handler for given set of types"""
            if not isinstance(types, (list, tuple)):
                types = [types]
            for type in types:
                self[type] = handler
            if handler.isOutput:
                self.all_output_handlers.append(handler)

        def registerReturn(self, handler):
            """Register this handler as the default return-type handler"""
            if isinstance(handler, (str, unicode)):
                self.preferredOutput = handler
                self.output_handler = None
            else:
                self.preferredOutput = None
                self.output_handler = handler

    GLOBAL_REGISTRY = HandlerRegistry(plugins.FormatHandler.match)
    formathandler.FormatHandler.TYPE_REGISTRY = GLOBAL_REGISTRY

    class ArrayDatatype(object):
        """Mix-in for array datatype classes

        The ArrayDatatype marker essentially is used to mark a particular argument
        as having an "array" type, which means that it is eligible for handling
        via the arrays sub-package and its registered handlers.
        """

        typeConstant = None
        handler = GLOBAL_REGISTRY
        getHandler = GLOBAL_REGISTRY.__call__
        returnHandler = GLOBAL_REGISTRY.get_output_handler
        isAccelerated = False

        @classmethod
        def getRegistry(cls):
            """Get our handler registry"""
            return cls.handler

        @classmethod
        @logs.logOnFailDec(_log)
        def from_param(cls, value, typeConstant=None):
            """Given a value in a known data-pointer type, convert to a ctypes pointer"""
            return cls.getHandler(value).from_param(value, cls.typeConstant)

        @classmethod
        def get_ffi_argtype(cls):
            """Declare our ffi calling-convention type (PyPy ctypes hook)

            PyPy's pure-Python ``_ctypes`` asks each argument type for its libffi
            type when it builds a foreign function from a raw address (the path
            PyOpenGL uses for extension/proc-address entry points).  The bare
            ``ArrayDatatype`` marker is not itself a ctypes type, but its
            ``from_param`` always yields a plain data pointer, so a ``void *``
            ffi type is the correct declaration.  CPython's C ``ctypes`` never
            calls this hook, so it is inert there.
            """
            return ctypes.c_void_p.get_ffi_argtype()

        @classmethod 
        @logs.logOnFailDec(_log)
        def dataPointer(cls, value):
            """Given a value in a known data-pointer type, return long for pointer"""
            try:
                return cls.getHandler(value).dataPointer(value)
            except Exception:
                _log.warning(
                    """Failure in dataPointer for %s instance %s""",
                    type(value),
                    value,
                )
                raise

        @classmethod 
        @logs.logOnFailDec(_log)
        def voidDataPointer(cls, value):
            """Given value in a known data-pointer type, return void_p for pointer"""
            pointer = cls.dataPointer(value)
            try:
                return ctypes.c_void_p(pointer)
            except TypeError:
                return pointer

        @classmethod 
        @logs.logOnFailDec(_log)
        def typedPointer(cls, value):
            """Return a pointer-to-base-type pointer for given value"""
            return ctypes.cast(cls.dataPointer(value), ctypes.POINTER(cls.baseType))

        @classmethod 
        @logs.logOnFailDec(_log)
        def asArray(cls, value, typeCode=None):
            """Given a value, convert to preferred array representation"""
            return cls.getHandler(value).asArray(value, typeCode or cls.typeConstant)

        @classmethod 
        @logs.logOnFailDec(_log)
        def arrayToGLType(cls, value):
            """Given a data-value, guess the OpenGL type of the corresponding pointer

            Note: this is not currently used in PyOpenGL and may be removed
            eventually.
            """
            return cls.getHandler(value).arrayToGLType(value)

        @classmethod 
        @logs.logOnFailDec(_log)
        def arraySize(cls, value, typeCode=None):
            """Given a data-value, calculate dimensions for the array (number-of-units)"""
            return cls.getHandler(value).arraySize(value, typeCode or cls.typeConstant)

        @classmethod 
        @logs.logOnFailDec(_log)
        def unitSize(cls, value, typeCode=None):
            """Determine unit size of an array (if possible)

            Uses our local type if defined, otherwise asks the handler to guess...
            """
            return cls.getHandler(value).unitSize(value, typeCode or cls.typeConstant)

        @classmethod 
        @logs.logOnFailDec(_log)
        def zeros(cls, dims, typeCode=None):
            """Allocate a return array of the given dimensions filled with zeros"""
            return cls.returnHandler().zeros(dims, typeCode or cls.typeConstant)

        @classmethod 
        @logs.logOnFailDec(_log)
        def dimensions(cls, value):
            """Given a data-value, get the dimensions (assumes full structure info)"""
            return cls.getHandler(value).dimensions(value)

        @classmethod 
        @logs.logOnFailDec(_log)
        def arrayByteCount(cls, value):
            """Given a data-value, try to determine number of bytes it's final form occupies

            For most data-types this is arraySize() * atomic-unit-size
            """
            return cls.getHandler(value).arrayByteCount(value)

    # the final array data-type classes...
    class GLclampdArray(ArrayDatatype, ctypes.POINTER(_types.GLclampd)):
        """Array datatype for GLclampd types"""

        baseType = _types.GLclampd
        typeConstant = _types.GL_DOUBLE

    class GLclampfArray(ArrayDatatype, ctypes.POINTER(_types.GLclampf)):
        """Array datatype for GLclampf types"""

        baseType = _types.GLclampf
        typeConstant = _types.GL_FLOAT

    class GLfloat16Array(ArrayDatatype, ctypes.POINTER(_types.GLushort)):
        """Array datatype for float16 as GLushort types"""

        baseType = _types.GLushort
        typeConstant = _types.GL_HALF_FLOAT

    class GLfloatArray(ArrayDatatype, ctypes.POINTER(_types.GLfloat)):
        """Array datatype for GLfloat types"""

        baseType = _types.GLfloat
        typeConstant = _types.GL_FLOAT

    class GLdoubleArray(ArrayDatatype, ctypes.POINTER(_types.GLdouble)):
        """Array datatype for GLdouble types"""

        baseType = _types.GLdouble
        typeConstant = _types.GL_DOUBLE

    class GLbyteArray(ArrayDatatype, ctypes.POINTER(_types.GLbyte)):
        """Array datatype for GLbyte types"""

        baseType = _types.GLbyte
        typeConstant = _types.GL_BYTE

    class GLcharArray(ArrayDatatype, ctypes.c_char_p):
        """Array datatype for ARB extension pointers-to-arrays"""

        baseType = _types.GLchar
        typeConstant = _types.GL_BYTE

    GLcharARBArray = GLcharArray

    class GLshortArray(ArrayDatatype, ctypes.POINTER(_types.GLshort)):
        """Array datatype for GLshort types"""

        baseType = _types.GLshort
        typeConstant = _types.GL_SHORT

    class GLintArray(ArrayDatatype, ctypes.POINTER(_types.GLint)):
        """Array datatype for GLint types"""

        baseType = _types.GLint
        typeConstant = _types.GL_INT

    class GLubyteArray(ArrayDatatype, ctypes.POINTER(_types.GLubyte)):
        """Array datatype for GLubyte types"""

        baseType = _types.GLubyte
        typeConstant = _types.GL_UNSIGNED_BYTE

    GLbooleanArray = GLubyteArray

    class GLushortArray(ArrayDatatype, ctypes.POINTER(_types.GLushort)):
        """Array datatype for GLushort types"""

        baseType = _types.GLushort
        typeConstant = _types.GL_UNSIGNED_SHORT

    class GLuintArray(ArrayDatatype, ctypes.POINTER(_types.GLuint)):
        """Array datatype for GLuint types"""

        baseType = _types.GLuint
        typeConstant = _types.GL_UNSIGNED_INT

    class GLint64Array(ArrayDatatype, ctypes.POINTER(_types.GLint64)):
        """Array datatype for GLint64 types"""

        baseType = _types.GLint64
        typeConstant = _types.GL_INT64

    class GLuint64Array(ArrayDatatype, ctypes.POINTER(_types.GLuint64)):
        """Array datatype for GLuint types"""

        baseType = _types.GLuint64
        typeConstant = _types.GL_UNSIGNED_INT64

    class GLintptrArray(ArrayDatatype, ctypes.POINTER(_types.GLintptr)):
        """Array datatype for GLintptr types (buffer offsets, VDPAU handles)

        As wide as a pointer, which is what distinguishes it from
        GLint64Array: the two agree on a 64-bit build and not on a 32-bit one.
        """

        baseType = _types.GLintptr
        typeConstant = GL_1_1.GL_INTPTR

    class GLsizeiptrArray(ArrayDatatype, ctypes.POINTER(_types.GLsizeiptr)):
        """Array datatype for GLsizeiptr types (buffer sizes)"""

        baseType = _types.GLsizeiptr
        typeConstant = GL_1_1.GL_SIZEIPTR

    class GLenumArray(ArrayDatatype, ctypes.POINTER(_types.GLenum)):
        """Array datatype for GLenum types"""

        baseType = _types.GLenum
        typeConstant = _types.GL_UNSIGNED_INT

    class GLsizeiArray(ArrayDatatype, ctypes.POINTER(_types.GLsizei)):
        """Array datatype for GLsizei types"""

        baseType = _types.GLsizei
        typeConstant = _types.GL_INT

    class GLvoidpArray(ArrayDatatype, ctypes.POINTER(_types.GLvoid)):
        """Array datatype for GLenum types"""

        baseType = _types.GLvoidp
        typeConstant = _types.GL_VOID_P

    class GLfixedArray(ArrayDatatype, ctypes.POINTER(_types.GLfixed)):
        baseType = _types.GLfixed
        typeConstant = _types.GL_FIXED

else:
    # Cython-coded array handler
    _log.debug("Using accelerated ArrayDatatype")
    ArrayDatatype = ADT(None, None)
    GLclampdArray = ADT(GL_1_1.GL_DOUBLE, _types.GLclampd)
    GLclampfArray = ADT(GL_1_1.GL_FLOAT, _types.GLclampf)
    GLdoubleArray = ADT(GL_1_1.GL_DOUBLE, _types.GLdouble)
    GLfloat16Array = ADT(GL_1_1.GL_HALF_FLOAT, _types.GLushort)
    GLfloatArray = ADT(GL_1_1.GL_FLOAT, _types.GLfloat)
    GLbyteArray = ADT(GL_1_1.GL_BYTE, _types.GLbyte)
    GLcharArray = GLcharARBArray = ADT(GL_1_1.GL_BYTE, _types.GLchar)
    GLshortArray = ADT(GL_1_1.GL_SHORT, _types.GLshort)
    GLintArray = ADT(GL_1_1.GL_INT, _types.GLint)
    GLubyteArray = GLbooleanArray = ADT(GL_1_1.GL_UNSIGNED_BYTE, _types.GLubyte)
    GLushortArray = ADT(GL_1_1.GL_UNSIGNED_SHORT, _types.GLushort)
    GLuintArray = ADT(GL_1_1.GL_UNSIGNED_INT, _types.GLuint)
    GLint64Array = ADT(GL_1_1.GL_INT64, _types.GLint64)
    GLuint64Array = ADT(GL_1_1.GL_UNSIGNED_INT64, _types.GLuint64)
    GLintptrArray = ADT(GL_1_1.GL_INTPTR, _types.GLintptr)
    GLsizeiptrArray = ADT(GL_1_1.GL_SIZEIPTR, _types.GLsizeiptr)
    GLenumArray = ADT(GL_1_1.GL_UNSIGNED_INT, _types.GLenum)
    GLsizeiArray = ADT(GL_1_1.GL_INT, _types.GLsizei)
    GLvoidpArray = ADT(_types.GL_VOID_P, _types.GLvoidp)
    GLfixedArray = ADT(_types.GL_FIXED, _types.GLfixed)

EGLAttribArray = GLintArray


GL_CONSTANT_TO_ARRAY_TYPE = {
    GL_1_1.GL_HALF_FLOAT: GLfloat16Array,
    GL_1_1.GL_DOUBLE: GLclampdArray,
    GL_1_1.GL_FLOAT: GLclampfArray,
    GL_1_1.GL_FLOAT: GLfloatArray,
    GL_1_1.GL_DOUBLE: GLdoubleArray,
    GL_1_1.GL_BYTE: GLbyteArray,
    GL_1_1.GL_SHORT: GLshortArray,
    GL_1_1.GL_INT: GLintArray,
    GL_1_1.GL_UNSIGNED_BYTE: GLubyteArray,
    GL_1_1.GL_UNSIGNED_SHORT: GLushortArray,
    GL_1_1.GL_UNSIGNED_INT: GLuintArray,
    GL_1_1.GL_UNSIGNED_INT64: GLuint64Array,
    GL_1_1.GL_INT64: GLint64Array,
    _types.GL_FIXED: GLfixedArray,
    GL_1_1.GL_INTPTR: GLintptrArray,
    GL_1_1.GL_SIZEIPTR: GLsizeiptrArray,
    # GL_1_1.GL_UNSIGNED_INT : GLenumArray,
}


#: Every array class by the ctypes element type it holds, built once.  A
#: declaration that names ``ctypes.POINTER(GLintptr)`` rather than
#: ``arrays.GLintptrArray`` still describes an array of that element, and this
#: is how the conversion for it is found.
_BY_ELEMENT = None


def arrayTypeForElement(element):
    """The array class whose elements are ``element``, or ``None``.

    ``None`` is an answer rather than an error: not every ctypes type an
    argument may be declared as has an array class, and the caller decides what
    to do about that.
    """
    global _BY_ELEMENT
    if _BY_ELEMENT is None:
        found = {}
        for name, value in list(globals().items()):
            if not name.endswith('Array'):
                continue
            baseType = getattr(value, 'baseType', None)
            if baseType is not None and hasattr(value, 'asArray'):
                found.setdefault(baseType, value)
        _BY_ELEMENT = found
    return _BY_ELEMENT.get(element)
