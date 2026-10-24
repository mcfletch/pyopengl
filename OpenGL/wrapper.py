"""Wrappers that give ctypes OpenGL functions a natural Python interface"""

import ctypes, logging
from OpenGL import platform, error, _configflags
from OpenGL._configflags import STORE_POINTERS, ERROR_ON_COPY, SIZE_1_ARRAY_UNPACK
from OpenGL import converters
from OpenGL.converters import DefaultCConverter
from OpenGL.converters import returnCArgument, returnPyArgument
from OpenGL.latebind import LateBind
from OpenGL.arrays import arrayhelpers, arraydatatype
from OpenGL._bytes import short_repr_tuple
from OpenGL._null import NULL
from OpenGL._string_array import StringArray

from OpenGL import acceleratesupport

_log = logging.getLogger('OpenGL.wrapper')
assert platform
cWrapper = None
if acceleratesupport.ACCELERATE_AVAILABLE:
    try:
        from OpenGL_accelerate.latebind import LateBind
        from OpenGL_accelerate.wrapper import (
            Wrapper as cWrapper,
            CArgCalculator,
            PyArgCalculator,
            CArgumentCalculator,
            MultiReturn,
        )
    except ImportError as err:
        _log.warning(
            """OpenGL_accelerate seems to be installed, but unable to import expected wrapper entry points!"""
        )

if not STORE_POINTERS:
    if not ERROR_ON_COPY:
        _log.error(
            """You've specified (not STORE_POINTERS) yet ERROR_ON_COPY is False, this would cause segfaults, so (not STORE_POINTERS) is being ignored"""
        )
        STORE_POINTERS = True


def asList(o):
    """Convert to a list if not already one"""
    if not isinstance(o, list):
        return list(o)
    return o


def none_or_pass(incoming, function, arguments):
    return incoming


none_or_pass.optional = True


def attach_arguments(err, cArguments):
    """Attach the arguments the call was about to make to ``err``.

    A ctypes conversion error names the argument it could not convert but
    not its value, so the converted arguments are added to the error.  They
    are shortened, because a GL call's arguments are often a mesh or a
    texture, and formatting one in full produces megabytes of digits.  See
    :func:`OpenGL._bytes.short_repr` and
    https://github.com/mcfletch/pyopengl/issues/114.
    """
    err.args = err.args + (short_repr_tuple(cArguments),)


class Wrapper(LateBind):
    """Wrapper around a ctypes cFunction object providing SWIG-like hooks

    Attributes:

        wrappedOperation - base operation, normally a ctypes function
            with data-types and error-checking specified
        pyConverters - converters for incoming Python arguments,
            provide 1:1 mapping to incoming Python arguments, can
            suppress an argument from the argument-set as well
                see setPyConverter
        pyConverterNames - caching/storage of the argument names
            for the Python converters
        cConverters - converters for incoming C-level arguments
            produce Python-level objects in 1:1 mapping to ctypes
            arguments from pyConverters results
                see setCConverter
        cResolvers - converters turning Python-level objects into
            ctypes-compatible data-types
                see setCResolver

    Generic Attributes:

        {ARG1}_LOOKUP_{ARG2} - lookup dictionaries to provide sizes for
            ARG1 output value from the value of ARG2, provided for
            documentation/reference
        {ARG1}_FROM_{ARG2} - lookup functions to provide sizes for ARG1
            output value from the value of ARG2, provided for
            documentation/reference
    """

    localProperties = (
        'wrappedOperation',
        '__file__',
        'pyConverters',
        'pyConverterNames',
        'cConverters',
        'cResolvers',
        'storeValues',
        'returnValues',
        '_finalCall',
    )

    def __init__(self, wrappedOperation):
        """Initialise the wrapper, storing wrappedOperation"""
        if isinstance(wrappedOperation, Wrapper):
            wrappedOperation = wrappedOperation.wrappedOperation
        self.wrappedOperation = wrappedOperation

    def __getattr__(self, key):
        """Delegate attribute lookup to our wrappedOperation"""
        if key != 'wrappedOperation':
            return getattr(self.wrappedOperation, key)
        raise AttributeError(key)

    def __nonzero__(self):
        """Is this function/wrapper available?"""
        return bool(self.wrappedOperation)

    __bool__ = __nonzero__

    def __setattr__(self, key, value):
        """Forward attribute setting to our wrappedOperation"""
        if key in self.localProperties:
            super(Wrapper, self).__setattr__(key, value)
        else:
            return setattr(self.wrappedOperation, key, value)

    def pyArgNames(self):
        """The names of the arguments a Python caller passes, in order

        These are the C argument names, minus the ones ``setPyConverter``
        removed, such as a count taken from an array's length or an output the
        wrapper allocates.  The installed converters do not change the result.
        With ``ERROR_ON_COPY`` an array is passed through without a converter,
        and the call signature is the same.  Use this attribute to read a
        wrapper's signature.  ``pyConverterNames`` exists only after a
        converter has been set.
        """
        argNames = getattr(self, 'pyConverterNames', None)
        if argNames is None:
            argNames = self.wrappedOperation.argNames
        return list(argNames)

    def pyArgIndex(self, argName):
        """Return the Python-argument index for the given argument name"""
        argNames = self.pyArgNames()
        try:
            return argNames.index(argName)
        except (ValueError, IndexError):
            raise KeyError(
                """No argument %r in argument list %r""" % (argName, argNames)
            ) from None

    def cArgIndex(self, argName):
        """Return the C-argument index for the given argument name"""
        argNames = self.wrappedOperation.argNames
        try:
            return asList(argNames).index(argName)
        except (ValueError, IndexError):
            raise KeyError(
                """No argument %r in argument list %r""" % (argName, argNames)
            ) from None

    def setOutput(
        self,
        outArg,
        size=(1,),
        pnameArg=None,
        arrayType=None,
        oldStyleReturn=SIZE_1_ARRAY_UNPACK,
        orPassIn=False,
    ):
        """Set the given argName to be an output array

        size - either a tuple compatible with arrayType.zeros or
            a function taking pname to produce such a value.
        arrayType - array data-type used to generate the output
            array using the zeros class method...
        pnameArg - optional argument passed into size function, that
            is, the name of the argument whose *value* will be passed
            to the size function, often the name of an input argument
            to be "sized" to match the output argument.
        """
        if arrayType is None:
            # figure out from self.wrappedOperation's argtypes
            index = self.cArgIndex(outArg)
            arrayType = self.wrappedOperation.argtypes[index]
            if not hasattr(arrayType, 'asArray'):
                if arrayType == ctypes.c_void_p:
                    from OpenGL.arrays import GLubyteArray

                    arrayType = GLubyteArray
                else:
                    raise TypeError(
                        "Should only have array types for output parameters %s on %s is %r"
                        % (
                            outArg,
                            self.wrappedOperation.__name__,
                            arrayType,
                        )
                    )
        if pnameArg is None:
            assert not callable(size)
            if orPassIn:
                cls = converters.OutputOrInput
            else:
                cls = converters.Output
            conv = cls(
                name=outArg,
                size=size,
                arrayType=arrayType,
            )
        else:
            if isinstance(size, dict):
                setattr(self, '%s_LOOKUP_%s' % (outArg, pnameArg), size)
                size = size.__getitem__
            else:
                setattr(self, '%s_FROM_%s' % (outArg, pnameArg), size)
            assert callable(size)
            if orPassIn:
                cls = converters.SizedOutputOrInput
            else:
                cls = converters.SizedOutput
            conv = cls(
                name=outArg,
                specifier=pnameArg,
                lookup=size,
                arrayType=arrayType,
            )
        if oldStyleReturn:
            returnObject = conv.oldStyleReturn
        else:
            returnObject = converters.returnCArgument(outArg)
        if orPassIn:
            self.setPyConverter(outArg, none_or_pass)
        else:
            self.setPyConverter(outArg)
        return self.setCConverter(
            outArg,
            conv,
        ).setReturnValues(returnObject)

    def typeOfArg(self, outArg):
        """Retrieve the defined data-type for the given outArg (name)"""
        index = self.cArgIndex(outArg)
        return self.wrappedOperation.argtypes[index]

    if not ERROR_ON_COPY:

        def setInputArraySize(self, argName, size=None):
            """Decorate function with vector-handling code for a single argument

            This is the version used when OpenGL.ERROR_ON_COPY is False.  It
            converts the named argument to the passed array type, and checks
            that the array matches size when size is given.

            When OpenGL.ERROR_ON_COPY is True, a simpler version is used.  It
            wraps the argument only when a size check is requested.
            """
            arrayType = self.typeOfArg(argName)
            pointerCConverter = None
            if not hasattr(arrayType, 'asArray'):
                if arrayType == ctypes.c_void_p:
                    # special case, we will convert to a void * array...
                    #
                    # ...unless the caller passed an integer, which for a
                    # `const void *` parameter is a byte offset into the bound
                    # buffer rather than data to upload.  See
                    # `arraydatatype.buffer_offset`.
                    self.setPyConverter(
                        argName,
                        converters.CallFuncPyConverter(
                            arraydatatype.as_offset_or_array
                        ),
                    )
                    self.setCConverter(argName, converters.getPyArgsName(argName))
                    return self
                element = getattr(arrayType, '_type_', None)
                if element is not None:
                    byElement = arraydatatype.arrayTypeForElement(element)
                    if byElement is not None:
                        # A pointer to a type an array class covers.  The
                        # declaration names the pointer type instead of the
                        # array type (GLintptr and GLsizeiptr parameters do
                        # this), and the array class still does the conversion.
                        arrayType = byElement
                        pointerCConverter = converters.getPyArgsPointer(
                            argName, byElement)
                    elif hasattr(element, '_type_'):
                        # is a ctypes array-of-pointers data-type...
                        # requires special handling no matter what...
                        #
                        # Only when the element is itself a pointer.  A simple
                        # ctypes type also has a ``_type_``, its struct format
                        # character, so testing for the attribute alone would
                        # leave every pointer-to-simple-type unconverted.
                        if hasattr(element, 'contents') or hasattr(
                            getattr(element, '_type_', None), '_type_'
                        ):
                            return self
                if not hasattr(arrayType, 'asArray'):
                    raise TypeError(
                        "Should only have array types for output parameters: got %s"
                        % (arrayType,)
                    )
            if size is not None:
                self.setPyConverter(
                    argName, arrayhelpers.asArrayTypeSize(arrayType, size)
                )
            else:
                self.setPyConverter(argName, arrayhelpers.asArrayType(arrayType))
            self.setCConverter(
                argName, pointerCConverter or converters.getPyArgsName(argName)
            )
            return self

    else:

        def setInputArraySize(self, argName, size=None):
            """Decorate function with vector-handling code for a single argument

            With ERROR_ON_COPY, the declared type does the conversion wherever
            it can.  An array class's ``from_param`` accepts any object that
            already has a data pointer and refuses one that would need a copy.
            An extra converter would repeat that check and add a call per
            array argument per draw.

            Two cases still get a converter.  The first is a size, because the
            type does not check sizes.  The second is a parameter declared as a
            bare pointer, as GLintptr and GLsizeiptr parameters are.  The
            ctypes pointer type refuses every array, so the array class for
            the pointer's element converts it instead, and that class also
            refuses a copy.
            """
            arrayType = self.typeOfArg(argName)
            if not hasattr(arrayType, 'asArray'):
                element = getattr(arrayType, '_type_', None)
                byElement = (
                    arraydatatype.arrayTypeForElement(element)
                    if element is not None
                    else None
                )
                if byElement is None:
                    # No array class converts this type.  ERROR_ON_COPY forbids
                    # copies and does not require a conversion, so the argument
                    # is passed as declared.
                    return self
                if size is not None:
                    self.setPyConverter(
                        argName, arrayhelpers.asArrayTypeSize(byElement, size)
                    )
                else:
                    self.setPyConverter(
                        argName, arrayhelpers.asArrayType(byElement)
                    )
                self.setCConverter(
                    argName, converters.getPyArgsPointer(argName, byElement)
                )
                return self
            if size is not None:
                # return value is always the source array...
                self.setPyConverter(
                    argName, arrayhelpers.asArrayTypeSize(arrayType, size)
                )
                self.setCConverter(argName, converters.getPyArgsName(argName))
            return self

    def setInputArrayCount(self, argName, countArg, multiplier=1):
        """Convert an input array, refusing fewer than countArg * multiplier elements

        argName - the array argument
        countArg - the argument giving how many items the driver reads
        multiplier - elements per item: ``glViewportArrayv`` reads four
            floats for each of ``count`` viewports

        A longer array is accepted, since the driver reads only the stated
        count.  A ``GLchar *const *`` argument is counted in strings, with a
        multiplier of one.  A pointer array the caller built is passed without
        a check.  With ``ARRAY_SIZE_CHECKING`` off, a numeric array is
        converted without a check, as ``setInputArraySize(argName, None)``
        does.  Strings are counted in both cases, for the reason in the
        comment below.
        """
        arrayType = self.typeOfArg(argName)
        if isinstance(arrayType, type) and issubclass(arrayType, StringArray):
            # A list of strings counts itself; the argument type converts it.
            #
            # Checked whatever ``ARRAY_SIZE_CHECKING`` says.  PyOpenGL
            # allocates the pointer array the driver reads, sized by the
            # list's length.  The flag covers arrays the caller owns, and a
            # count larger than the list would read past the end of this
            # buffer.
            self.setPyConverter(
                argName, arrayhelpers.StringArrayCountChecked(countArg)
            )
            self.setCConverter(argName, converters.getPyArgsName(argName))
            return self
        if not _configflags.ARRAY_SIZE_CHECKING:
            return self.setInputArraySize(argName, None)
        if not hasattr(arrayType, 'asArray'):
            raise TypeError(
                "%s.%s is declared %s, which has no array conversion to measure"
                % (self.wrappedOperation.__name__, argName, arrayType)
            )
        self.setPyConverter(
            argName,
            arrayhelpers.AsArrayTypedCountChecked(arrayType, countArg, multiplier),
        )
        self.setCConverter(argName, converters.getPyArgsName(argName))
        return self

    def setPyConverter(self, argName, function=NULL):
        """Set Python-argument converter for given argument

        argName - the argument name which will be coerced to a usable internal
            format using the function provided.
        function - None (indicating a simple copy), NULL (default) to eliminate
            the argument from the Python argument-list, or a callable object with
            the signature:

                converter(arg, wrappedOperation, args)

            where arg is the particular argument on which the convert is working,
            wrappedOperation is the underlying wrapper, and args is the set of
            original Python arguments to the function.

        Note that you need exactly the same number of pyConverters as Python
        arguments.
        """
        if not hasattr(self, 'pyConverters'):
            self.pyConverters = [None] * len(self.wrappedOperation.argNames)
            self.pyConverterNames = list(self.wrappedOperation.argNames)
        try:
            i = asList(self.pyConverterNames).index(argName)
        except ValueError:
            raise AttributeError(
                """No argument named %r left in pyConverters for %r: %s"""
                % (
                    argName,
                    self.wrappedOperation.__name__,
                    self.pyConverterNames,
                )
            ) from None
        if function is NULL:
            del self.pyConverters[i]
            del self.pyConverterNames[i]
        else:
            self.pyConverters[i] = function
        return self

    def setCConverter(self, argName, function):
        """Set C-argument converter for a given argument

        argName - the argument name whose C-compatible representation will
            be calculated with the passed function.
        function - None (indicating a simple copy), a non-callable object to
            be copied into the result-list itself, or a callable object with
            the signature:

                converter( pyArgs, index, wrappedOperation )

            where pyArgs is the set of passed Python arguments, with the
            pyConverters already applied, index is the index of the C argument
            and wrappedOperation is the underlying function.

        C-argument converters expand or contract a Python argument list
        (pyArgs) to match the number of arguments the ctypes baseOperation
        expects.  A "null" C-argument converter is not allowed, because the
        C-level function needs a value for every parameter.
        """
        if not hasattr(self, 'cConverters'):
            self.cConverters = [None] * len(self.wrappedOperation.argNames)
        try:
            if not isinstance(self.wrappedOperation.argNames, list):
                self.wrappedOperation.argNames = list(self.wrappedOperation.argNames)
            i = asList(self.wrappedOperation.argNames).index(argName)
        except ValueError:
            raise AttributeError(
                """No argument named %r left in cConverters: %s"""
                % (
                    argName,
                    self.wrappedOperation.argNames,
                )
            ) from None
        if self.cConverters[i] is not None:
            raise RuntimeError(
                "Double wrapping of output parameter: %r on %s"
                % (argName, self.__name__)
            )
        self.cConverters[i] = function
        return self

    def setCResolver(self, argName, function=NULL):
        """Set the C-argument resolver for a given argument"""
        if not hasattr(self, 'cResolvers'):
            self.cResolvers = [None] * len(self.wrappedOperation.argNames)
        try:
            if not isinstance(self.wrappedOperation.argNames, list):
                self.wrappedOperation.argNames = list(self.wrappedOperation.argNames)
            i = asList(self.wrappedOperation.argNames).index(argName)
        except ValueError:
            raise AttributeError(
                """No argument named %r left in cConverters: %s"""
                % (
                    argName,
                    self.wrappedOperation.argNames,
                )
            ) from None
        if function is NULL:
            del self.cResolvers[i]
        else:
            self.cResolvers[i] = function
        return self

    def setStoreValues(self, function=NULL):
        """Set the storage-of-arguments function for the whole wrapper"""
        if function is NULL or ERROR_ON_COPY and not STORE_POINTERS:
            try:
                del self.storeValues
            except Exception:
                pass
        else:
            self.storeValues = function
        return self

    def setReturnValues(self, function=NULL):
        """Set the return-of-results function for the whole wrapper"""
        if function is NULL:
            try:
                del self.returnValues
            except Exception:
                pass
        else:
            if hasattr(self, 'returnValues'):
                if isinstance(self.returnValues, MultiReturn):
                    self.returnValues.append(function)
                else:
                    self.returnValues = MultiReturn(self.returnValues, function)
            else:
                self.returnValues = function
        return self

    def finalise(self):
        """Finalise our various elements into simple index-based operations"""
        for attribute in ('pyConverters', 'cConverters', 'cResolvers'):
            value = getattr(self, attribute, None)
            if value is not None:
                for i, item in enumerate(value):
                    if hasattr(item, 'finalise'):
                        try:
                            item.finalise(self)
                        except Exception as err:
                            raise error.Error(
                                """Error finalising item %s in %s for %s (%r): %s"""
                                % (
                                    i,
                                    attribute,
                                    self,
                                    item,
                                    err,
                                )
                            ) from err
        if hasattr(self, 'cConverters'):
            for i, converter in enumerate(self.cConverters):
                if isinstance(converter, (type(None), DefaultCConverter)):
                    self.cConverters[i] = DefaultCConverter(
                        self.pyArgIndex(self.argNames[i])
                    )
        for attribute in (
            'storeValues',
            'returnValues',
        ):
            item = getattr(self, attribute, None)
            if hasattr(item, 'finalise'):
                item.finalise(self)
        callFunction = self.finaliseCall()
        if not callFunction:
            raise RuntimeError("""Missing finalised call type for %s""" % (self,))
        else:
            # self.__class__.finalize = lambda *args: callFunction
            # self.__call__ = callFunction
            # self.__class__.__call__ = callFunction
            # self.__class__.set_call( callFunction )
            # self.__class__.__dict__[ '__call__' ] = callFunction
            # print 'setting class call', callFunction
            self.setFinalCall(callFunction)
            return callFunction
        # return self

    def finaliseCall(self):
        """Produce specialised versions of call for finalised wrapper object

        Returns a version of __call__ that does only the work this wrapper
        object needs.

        The body is a large set of expanded nested functions, one for each
        combination of the converters and hooks a wrapper can have.
        """
        pyConverters = getattr(self, 'pyConverters', None)
        cConverters = getattr(self, 'cConverters', None)
        cResolvers = getattr(self, 'cResolvers', None)
        wrappedOperation = self.wrappedOperation
        storeValues = getattr(self, 'storeValues', None)
        returnValues = getattr(self, 'returnValues', None)
        if pyConverters:
            if cWrapper:
                calculate_pyArgs = PyArgCalculator(
                    self,
                    pyConverters,
                )
            else:
                pyConverters_mapped = [
                    (i, converter, (converter is None))
                    for (i, converter) in enumerate(pyConverters)
                ]
                pyConverters_length = len(
                    [p for p in pyConverters if not getattr(p, 'optional', False)]
                )

                def calculate_pyArgs(args):
                    if pyConverters_length > len(args):
                        raise ValueError(
                            """%s requires %r arguments (%s), received %s: %s"""
                            % (
                                wrappedOperation.__name__,
                                pyConverters_length,
                                ", ".join(self.pyConverterNames),
                                len(args),
                                short_repr_tuple(args),
                            )
                        )
                    for index, converter, isNone in pyConverters_mapped:
                        if isNone:
                            yield args[index]
                        else:
                            try:
                                yield converter(args[index], self, args)
                            except IndexError as err:
                                yield NULL
                            except Exception as err:
                                if hasattr(err, 'args'):
                                    err.args += (converter,)
                                raise

        else:
            calculate_pyArgs = None
        if cConverters:
            if cWrapper:
                calculate_cArgs = CArgCalculator(self, cConverters)
            else:
                cConverters_mapped = [
                    (i, converter, callable(converter))
                    for (i, converter) in enumerate(cConverters)
                ]

                def calculate_cArgs(pyArgs):
                    for index, converter, canCall in cConverters_mapped:
                        if canCall:
                            try:
                                yield converter(pyArgs, index, self)
                            except Exception as err:
                                if hasattr(err, 'args'):
                                    err.args += (
                                        """Failure in cConverter %r""" % (converter),
                                        short_repr_tuple(pyArgs),
                                        index,
                                        self,
                                    )
                                raise
                        else:
                            yield converter

        else:
            calculate_cArgs = None
        if cResolvers:
            if cWrapper:
                calculate_cArguments = CArgumentCalculator(cResolvers)
            else:
                cResolvers_mapped = list(enumerate(cResolvers))

                def calculate_cArguments(cArgs):
                    for i, converter in cResolvers_mapped:
                        if converter is None:
                            yield cArgs[i]
                        else:
                            try:
                                yield converter(cArgs[i])
                            except Exception as err:
                                err.args += (converter,)
                                raise

        else:
            calculate_cArguments = None
        if cWrapper:
            return cWrapper(
                wrappedOperation,
                calculate_pyArgs=calculate_pyArgs,
                calculate_cArgs=calculate_cArgs,
                calculate_cArguments=calculate_cArguments,
                storeValues=storeValues,
                returnValues=returnValues,
            )
        if pyConverters:
            if cConverters:
                # create a map of index,converter, callable
                if cResolvers:
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
                else:
                    # null cResolvers
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = tuple(calculate_cArgs(pyArgs))
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
            else:
                # null cConverters
                if cResolvers:
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = pyArgs
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = pyArgs
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = pyArgs
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArgs = pyArgs
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
                else:
                    # null cResolvers
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArguments = pyArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArguments,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArguments,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArguments = pyArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArguments,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArguments = pyArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArguments,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = tuple(calculate_pyArgs(args))
                                cArguments = pyArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
        else:
            # null pyConverters
            if cConverters:
                if cResolvers:
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
                else:
                    # null cResolvers
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    pyArgs,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                pyArgs = args
                                cArgs = []
                                for index, converter in enumerate(cConverters):
                                    # move enumerate out...
                                    if not callable(converter):
                                        cArgs.append(converter)
                                    else:
                                        try:
                                            cArgs.append(converter(pyArgs, index, self))
                                        except Exception as err:
                                            if hasattr(err, 'args'):
                                                err.args += (
                                                    """Failure in cConverter %r"""
                                                    % (converter),
                                                    short_repr_tuple(pyArgs),
                                                    index,
                                                )
                                            raise
                                cArguments = cArgs
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = pyArgs
                                    raise err
                                return result

                            return wrapperCall
            else:
                # null cConverters
                if cResolvers:
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                cArgs = args
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = args
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    args,
                                    cArgs,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    args,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                cArgs = args
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = args
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    args,
                                    cArgs,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                cArgs = args
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = args
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    args,
                                    cArgs,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                cArgs = args
                                cArguments = tuple(calculate_cArguments(cArgs))
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArgs
                                    err.pyArgs = args
                                    raise err
                                return result

                            return wrapperCall
                else:
                    # null cResolvers
                    if storeValues:
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all possible operations"""
                                cArguments = args
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = args
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    args,
                                    cArguments,
                                )
                                return returnValues(
                                    result,
                                    self,
                                    args,
                                    cArguments,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues"""
                                cArguments = args
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = args
                                    raise err
                                # handle storage of persistent argument values...
                                storeValues(
                                    result,
                                    self,
                                    args,
                                    cArguments,
                                )
                                return result

                            return wrapperCall
                    else:  # null storeValues
                        if returnValues:

                            def wrapperCall(*args):
                                """Wrapper with all save storeValues"""
                                cArguments = args
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = args
                                    raise err
                                return returnValues(
                                    result,
                                    self,
                                    args,
                                    cArguments,
                                )

                            return wrapperCall
                        else:

                            def wrapperCall(*args):
                                """Wrapper with all save returnValues and storeValues"""
                                cArguments = args
                                try:
                                    result = wrappedOperation(*cArguments)
                                except ctypes.ArgumentError as err:
                                    attach_arguments(err, cArguments)
                                    raise
                                except error.GLError as err:
                                    err.cArgs = cArguments
                                    err.pyArgs = args
                                    raise err
                                return result

                            return wrapperCall

    #    def __call__( self, *args, **named ):
    #        """Finalise the wrapper before calling it"""
    #        try:
    #            return self._finalCall( *args, **named )
    #        except AttributeError, err:
    #            return self.finalise()( *args, **named )

    def _unspecialised__call__(self, *args):
        """Expand arguments, call the function, store values and check errors"""
        pyConverters = getattr(self, 'pyConverters', None)
        if pyConverters:
            if len(pyConverters) != len(args):
                raise ValueError(
                    """%s requires %r arguments (%s), received %s: %s"""
                    % (
                        self.wrappedOperation.__name__,
                        len(pyConverters),
                        ", ".join(self.pyConverterNames),
                        len(args),
                        short_repr_tuple(args),
                    )
                )
            pyArgs = []
            for converter, arg in zip(pyConverters, args):
                if converter is None:
                    pyArgs.append(arg)
                else:
                    pyArgs.append(converter(arg, self, args))
        else:
            pyArgs = args
        cConverters = getattr(self, 'cConverters', None)
        if cConverters:
            cArgs = []
            for index, converter in enumerate(cConverters):
                if not callable(converter):
                    cArgs.append(converter)
                else:
                    try:
                        cArgs.append(converter(pyArgs, index, self))
                    except Exception as err:
                        if hasattr(err, 'args'):
                            err.args += (
                                """Failure in cConverter %r""" % (converter),
                                short_repr_tuple(pyArgs),
                                index,
                                self,
                            )
                        raise
        else:
            cArgs = pyArgs
        cResolvers = getattr(self, 'cResolvers', None)
        if cResolvers:
            cArguments = []
            for converter, value in zip(cResolvers, cArgs):
                if converter is None:
                    cArguments.append(value)
                else:
                    cArguments.append(converter(value))
        else:
            cArguments = cArgs
        try:
            result = self.wrappedOperation(*cArguments)
        except ctypes.ArgumentError as err:
            attach_arguments(err, cArguments)
            raise
        except error.GLError as err:
            err.cArgs = cArgs
            err.pyArgs = pyArgs
            raise err
        storeValues = getattr(self, 'storeValues', None)
        if storeValues is not None:
            # handle storage of persistent argument values...
            storeValues(
                result,
                self,
                pyArgs,
                cArgs,
            )
        returnValues = getattr(self, 'returnValues', None)
        if returnValues is not None:
            return returnValues(
                result,
                self,
                pyArgs,
                cArgs,
            )
        else:
            return result


class MultiReturn(object):
    """The return of a wrapper with more than one output, in declared order."""

    def __init__(self, *children):
        self.children = list(children)

    def append(self, child):
        self.children.append(child)

    def finalise(self, wrapper):
        """Resolve each child's argument names to indices.

        The wrapper finalises its ``returnValues``.  With one output, that is
        the converter itself.  With several, it is this object, so the
        children are finalised only here.  Until then, a child that returns a
        named argument returns argument zero.
        """
        for child in self.children:
            if hasattr(child, 'finalise'):
                child.finalise(wrapper)

    def __call__(self, *args, **named):
        result = []
        for child in self.children:
            try:
                result.append(child(*args, **named))
            except Exception as err:
                err.args += (child, args, named)
                raise
        return result


def wrapper(wrappedOperation):
    """Create a Wrapper sub-class instance for the given wrappedOperation

    The subclass has the __doc__ and __name__ of the wrappedOperation, so the
    wrapper instance shows up as <functionname instance @ address> by default,
    and pydoc and similar tools show its docstring.
    """
    if isinstance(wrappedOperation, Wrapper):
        return wrappedOperation
    dict = {
        '__doc__': wrappedOperation.__doc__,
        '__slots__': ('wrappedOperation',),
    }
    cls = type(wrappedOperation.__name__, (Wrapper,), dict)
    if hasattr(wrappedOperation, '__module__'):
        cls.__module__ = wrappedOperation.__module__
    instance = cls(wrappedOperation)
    return instance
