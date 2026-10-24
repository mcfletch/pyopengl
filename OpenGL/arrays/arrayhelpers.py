"""Helper functions for wrapping array-using operations

These are functions intended to be used in wrapping
GL functions that deal with OpenGL array data-types.
"""

import OpenGL
import ctypes
from OpenGL import _configflags
from OpenGL import contextdata, error, converters
from OpenGL.arrays import arraydatatype
from OpenGL._bytes import bytes, unicode
import logging

_log = logging.getLogger('OpenGL.arrays.arrayhelpers')
from OpenGL import acceleratesupport

AsArrayTypedSizeChecked = None
if acceleratesupport.ACCELERATE_AVAILABLE:
    try:
        from OpenGL_accelerate.arraydatatype import AsArrayTypedSizeChecked
        from OpenGL_accelerate.wrapper import returnPyArgumentIndex
        from OpenGL_accelerate.arraydatatype import (
            AsArrayOfType,
            AsArrayTyped,
            AsArrayTypedSize,
        )
    except ImportError as err:
        _log.warning("Unable to load arrayhelpers accelerator from OpenGL_accelerate")
if AsArrayTypedSizeChecked is None:

    def returnPointer(
        result,
        baseOperation,
        pyArgs,
        cArgs,
    ):
        """Return the converted object as result of function

        Note: this is a hack that always returns pyArgs[0]!
        """
        return pyArgs[0]

    class AsArrayOfType(converters.PyConverter):
        """Given arrayName and typeName coerce arrayName to array of type typeName

        Installed under ``ERROR_ON_COPY`` as well.  The type passed to the
        driver comes from another argument, and this converter is the only
        check of the array against it.  Where they differ, ``asArray``
        refuses the copy.
        """

        argNames = ('arrayName', 'typeName')
        indexLookups = (
            ('arrayIndex', 'arrayName', 'pyArgIndex'),
            ('typeIndex', 'typeName', 'pyArgIndex'),
        )

        def __init__(self, arrayName='pointer', typeName='type'):
            self.arrayName = arrayName
            self.typeName = typeName

        def __call__(self, arg, wrappedOperation, args):
            """Get the arg as an array of the appropriate type"""
            # An integer here is a byte offset into the bound buffer, not a
            # value to upload.  This converter serves `glDrawElements` and the
            # pixel calls, whose data argument GL reads as an offset whenever
            # a buffer object is bound.  See
            # `OpenGL.arrays.arraydatatype.buffer_offset`.
            offset = arraydatatype.buffer_offset(arg)
            if offset is not None:
                return offset
            type = args[self.typeIndex]
            arrayType = arraydatatype.GL_CONSTANT_TO_ARRAY_TYPE[type]
            return arrayType.asArray(arg)

    class AsArrayTyped(converters.PyConverter):
        """Given arrayName and arrayType, convert arrayName to array of type

        Installed under ``ERROR_ON_COPY`` as well, for the same reason as
        :class:`AsArrayOfType`.  The wrapper sets the element type, not the
        caller.
        """

        argNames = ('arrayName', 'arrayType')
        indexLookups = (('arrayIndex', 'arrayName', 'pyArgIndex'),)

        def __init__(self, arrayName='pointer', arrayType=None):
            self.arrayName = arrayName
            self.arrayType = arrayType

        def __call__(self, arg, wrappedOperation, args):
            """Get the arg as an array of the appropriate type"""
            return self.arrayType.asArray(arg)

    class AsArrayTypedSize(converters.CConverter):
        """Given arrayName and arrayType, determine size of arrayName"""

        argNames = ('arrayName', 'arrayType')
        indexLookups = (('arrayIndex', 'arrayName', 'pyArgIndex'),)

        def __init__(self, arrayName='pointer', arrayType=None):
            self.arrayName = arrayName
            self.arrayType = arrayType

        def __call__(self, pyArgs, index, wrappedOperation):
            """Get the arg as an array of the appropriate type"""
            return self.arrayType.arraySize(pyArgs[self.arrayIndex])

else:
    returnPointer = returnPyArgumentIndex(0)


def asArrayType(typ, size=None):
    """Create PyConverter to get first argument as array of type

    Installed regardless of ``ERROR_ON_COPY``.  It is used where the wrapper
    sets the element type, not the caller.  ``glVertexPointerb`` passes GL_INT
    whatever array it receives, and a parameter declared as a bare pointer has
    no array class for ctypes to use.  Nothing later compares the array with
    the type passed to the driver.  Without this converter, the driver could
    receive an array of one element width while told another.  Under the flag,
    ``asArray`` refuses the copy.
    """
    return converters.CallFuncPyConverter(typ.asArray)


if not _configflags.ARRAY_SIZE_CHECKING:
    asArrayTypeSize = asArrayType
else:
    if AsArrayTypedSizeChecked:
        asArrayTypeSize = AsArrayTypedSizeChecked
    else:

        def asArrayTypeSize(typ, size):
            """Create PyConverter function to get array as type and check size

            Produces a raw function, not a PyConverter instance
            """
            # asArray = typ.asArray
            dataType = typ.typeConstant
            # arraySize = typ.arraySize
            expectedBytes = ctypes.sizeof(typ.baseType) * size

            def asArraySize(incoming, function, args):
                handler = typ.getHandler(incoming)
                result = handler.asArray(incoming, dataType)
                # check that the number of bytes expected is present...
                byteSize = handler.arrayByteCount(result)
                if byteSize != expectedBytes:
                    raise ValueError(
                        """Expected %r byte array, got %r byte array"""
                        % (
                            expectedBytes,
                            byteSize,
                        ),
                        incoming,
                    )
                return result

            return asArraySize


class AsArrayTypedCountChecked(converters.PyConverter):
    """Convert to ``arrayType``, refusing fewer than ``count * multiplier`` elements

    For inputs where another argument gives the number of items the driver
    reads.  ``glViewportArrayv(first, count, v)`` reads four floats for each
    of ``count`` viewports, so a shorter array makes the driver read past its
    end.  A longer array is accepted.  ``None`` is refused unless the count is
    zero, because the driver would read from a null pointer.
    """

    argNames = ('arrayType', 'countName', 'multiplier')
    indexLookups = (('countIndex', 'countName', 'pyArgIndex'),)

    def __init__(self, arrayType, countName, multiplier=1):
        self.arrayType = arrayType
        self.countName = countName
        self.multiplier = multiplier
        self.elementBytes = ctypes.sizeof(arrayType.baseType)

    def __call__(self, incoming, function, arguments):
        handler = self.arrayType.getHandler(incoming)
        result = handler.asArray(incoming, self.arrayType.typeConstant)
        expected = self.elementBytes * self.multiplier * arguments[self.countIndex]
        if result is None:
            if expected > 0:
                raise ValueError(
                    'Expected at least %r byte array, got None' % (expected,),
                    incoming,
                )
            return result
        counter = getattr(handler, 'arrayByteCount', None)
        # A bare number converts to a ctypes scalar (an array of one), which
        # its handler cannot measure.
        byteSize = counter(result) if counter is not None else ctypes.sizeof(result)
        if byteSize < expected:
            raise ValueError(
                """Expected at least %r byte array, got %r byte array"""
                % (expected, byteSize),
                incoming,
            )
        return result


class StringArrayCountChecked(converters.PyConverter):
    """Pass a ``GLchar *const *`` argument, refusing fewer strings than ``countName`` says

    The driver reads ``count`` pointers from the array.  Fewer strings make it
    read past the array's end.  ``None`` is a null pointer, refused unless the
    count is zero.  A pointer array the caller built is passed unchanged,
    because its length is unknown here.
    :func:`OpenGL._string_array.as_bytes_list` decides what counts as a
    string, and the argument type converts the value passed.
    """

    argNames = ('countName',)
    indexLookups = (('countIndex', 'countName', 'pyArgIndex'),)

    def __init__(self, countName):
        self.countName = countName

    def __call__(self, incoming, function, arguments):
        from OpenGL._string_array import as_bytes_list

        expected = arguments[self.countIndex]
        if incoming is None:
            if expected > 0:
                raise ValueError(
                    'Expected at least %r strings, got None' % (expected,), incoming
                )
            return incoming
        strings = as_bytes_list(incoming)
        if strings is not None and len(strings) < expected:
            raise ValueError(
                'Expected at least %r strings, got %r' % (expected, len(strings)),
                incoming,
            )
        return incoming


if not _configflags.ERROR_ON_COPY:

    def asVoidArray():
        """Create PyConverter returning incoming as an array of any type"""
        from OpenGL.arrays import ArrayDatatype

        return converters.CallFuncPyConverter(ArrayDatatype.asArray)

else:

    def asVoidArray():
        """If there's no copying allowed, we can use default passing"""
        return None


class storePointerType(object):
    """Store named pointer value in context indexed by constant

    pointerName - named pointer argument
    constant - constant used to index in the context storage

    Note: OpenGL.STORE_POINTERS can be set with ERROR_ON_COPY
    to ignore this storage operation.

    Stores the pyArgs (i.e. result of pyConverters) for the named
    pointer argument...
    """

    def __init__(self, pointerName, constant):
        self.pointerName = pointerName
        self.constant = constant

    def finalise(self, wrapper):
        self.pointerIndex = wrapper.pyArgIndex(self.pointerName)

    def __call__(self, result, baseOperation, pyArgs, cArgs):
        contextdata.setValue(self.constant, pyArgs[self.pointerIndex])


def setInputArraySizeType(baseOperation, size, type, argName=0):
    """Decorate function with vector-handling code for a single argument

    if OpenGL.ERROR_ON_COPY is False, then we return the
    named argument, converting to the passed array type,
    optionally checking that the array matches size.

    if OpenGL.ERROR_ON_COPY is True, then we will dramatically
    simplify this function, only wrapping if size is True, i.e.
    only wrapping if we intend to do a size check on the array.
    """
    from OpenGL import wrapper

    return wrapper.wrapper(baseOperation).setInputArraySize(argName, size)


def arraySizeOfFirstType(typ, default):
    unitSize = typ.unitSize

    def arraySizeOfFirst(pyArgs, index, baseOperation):
        """Return the array size of the first argument"""
        array = pyArgs[0]
        if array is None:
            return default
        else:
            return unitSize(array)

    return arraySizeOfFirst
