"""Base class for platform implementations
"""

import ctypes
from OpenGL.platform import ctypesloader
from OpenGL._bytes import as_8_bit
import sys, logging
from OpenGL import _configflags
from OpenGL import logs, MODULE_ANNOTATIONS
from typing import ClassVar

log = logging.getLogger(__name__)

#: The library an entry point belongs to, by the prefix of its name.
#:
#: Longest first, because ``glutInit`` also begins with ``glu``.
#:
#: The Khronos registry and the SGI headers assign these prefixes.  When a
#: library could not be loaded, the platform attribute for it is ``None``, and
#: every declaration in the module is built against ``None``.  The name prefix
#: is then the only way to tell which library was missing.
ENTRY_POINT_PREFIXES = (
    ('glut', 'GLUT'),
    ('glu', 'GLU'),
    ('gle', 'GLE'),
    ('egl', 'EGL'),
    ('wgl', 'GL'),
    ('glX', 'GL'),
    ('gl', 'GL'),
)

#: The package that provides each library, per operating system.
#:
#: Package names differ by distribution (see issues #54 and #59), so each
#: message lists several.
#:
#: GL has no entry.  A machine with no OpenGL library has no graphics driver,
#: and a package name would be the wrong advice.
LIBRARY_SOURCES = {
    'GLU': (
        'Debian and Ubuntu: libglu1-mesa; Fedora: mesa-libGLU; Arch: glu; '
        'Windows and macOS ship it'
    ),
    'GLUT': (
        'Debian and Ubuntu: freeglut3-dev; Fedora: freeglut; Arch: freeglut; '
        'macOS ships it; on Windows, pip install PyOpenGL[glut]'
    ),
    'GLE': (
        'Debian and Ubuntu: libgle3; Fedora: gle; on Windows, '
        'pip install PyOpenGL[glut] -- one download carries GLE as well'
    ),
    'EGL': (
        'it arrives with the graphics driver; on Windows it comes from an '
        'ANGLE build shipped beside the application'
    ),
}


#: The error text for an entry point that does not resolve without a context.
#:
#: Also used by :func:`OpenGL.extensions.alternate`, which reports the same
#: situation for a call with several possible names (such as the
#: framebuffer-object entry points) when none of them resolved.
NO_CONTEXT_EXPLANATION = (
    'no OpenGL context is current, and every entry point above GL 1.1 is '
    'resolved through the context -- so this says the call came before a '
    'context was created rather than that the driver lacks it. Create a '
    'context first, through GLUT, GLFW, pygame, Qt, EGL or whatever your '
    'program uses'
)


def library_for_entry_point(name):
    """The library ``name`` belongs to, or None for an unknown prefix.

    See :data:`ENTRY_POINT_PREFIXES` for why the name prefix is used.
    """
    for prefix, library in ENTRY_POINT_PREFIXES:
        if name.startswith(prefix):
            return library
    return None


def undefined_function_message(name, dll, has_context=None):
    """The error message for calling the undefined entry point ``name``.

    The message distinguishes three cases.

    A ``dll`` of ``None`` means the library was not found, so every entry
    point in it is undefined.  The message names the package to install.

    A loaded library with no current context means the entry point could not
    be resolved yet.  Above GL 1.1, addresses come from the context, so every
    such name is undefined until a context is current.  This is the usual
    case on Windows, where ``wglGetProcAddress`` needs a current context.  GLX
    resolves names without one, so the case is rarer on Linux.  The message
    says to create a context before the call.

    A loaded library with a current context and no entry point means the
    driver is too old or the machine lacks the extension.  There is nothing to
    install.

    ``has_context`` is ``None`` when it could not be determined, and is then
    treated as the third case.

    Every message ends by naming ``bool(name)``, the check callers use to test
    for an entry point before calling it.
    """
    if dll is None:
        library = library_for_entry_point(name)
        if library is None:
            what = 'the library it belongs to was not found on this machine'
        else:
            what = (
                'the %s library was not found on this machine, so every %s '
                'entry point is undefined' % (library, library)
            )
        source = LIBRARY_SOURCES.get(library)
        if source:
            what += ' (%s)' % (source,)
    elif has_context is False:
        what = NO_CONTEXT_EXPLANATION
    else:
        what = (
            'the library it belongs to does not export it, which is a driver '
            'too old for it or an extension this machine does not have, '
            'rather than a missing install'
        )
    return 'Attempt to call an undefined function %s: %s. Check bool(%s) ' \
           'before calling.' % (name, what, name)


def _context_is_current():
    """Whether a GL context is current, or None if that cannot be determined.

    Called only while building an error message, so the driver query runs
    only on a path that is already failing.  Any exception from the query
    returns None, so the original error is not replaced by another.
    """
    try:
        from OpenGL import platform

        return bool(platform.PLATFORM.GetCurrentContext())
    except Exception:  # noqa: BLE001 builds an error message, and must not replace the error
        return None


class lazy_property(object):
    """An attribute computed on first read, then cached on the instance

    Platform attributes are libraries, and finding a library loads it.
    Computing every attribute at import would load libraries the program never
    uses.
    """

    def __init__(self, function):
        self.fget = function
        self.__name__ = function.__name__
        self.__doc__ = function.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:
            # Read from the class, with no instance.  Return the descriptor, as
            # other Python descriptors do, so help(), inspect and documentation
            # builds can list the class's attributes without an instance.
            return self
        value = self.fget(obj)
        setattr(obj, self.__name__, value)
        return value


class _CheckContext(object):
    def __init__(self, func, ccisvalid):
        self.func = func
        self.ccisvalid = ccisvalid

    def __setattr__(self, key, value):
        if key not in ('func', 'ccisvalid'):
            return setattr(self.func, key, value)
        else:
            self.__dict__[key] = value

    def __repr__(self):
        if getattr(self.func, '__doc__', None):
            return self.func.__doc__
        else:
            return repr(self.func)

    def __getattr__(self, key):
        if key != 'func':
            return getattr(self.func, key)
        raise AttributeError(key)

    def __call__(self, *args, **named):
        if not self.ccisvalid():
            from OpenGL import error

            raise error.NoContext(self.func.__name__, args, named)
        return self.func(*args, **named)


def _find_module(exclude=(__name__,)):
    frame = sys._getframe()
    while frame and '__name__' in frame.f_globals:
        if exclude:
            if frame.f_globals['__name__'] not in exclude:
                return frame.f_globals['__name__']

        else:
            return frame.f_globals['__name__']
        frame = frame.f_back
    return None


def _also_core(functionName, module):
    """Whether a core version of ``module``'s API declares ``functionName``.

    ``module`` is the generated module the declaration came from, which
    identifies the API.  False when there is no module (a binding built by
    hand) or no declaration table (the hand-maintained GLU, GLUT and GLE).
    """
    if not module:
        return False
    from OpenGL import _declarations

    return functionName in _declarations.core_command_names(
        _declarations.api_of(module)
    )


class BasePlatform(object):
    """Base class for per-platform implementations

    Attributes of note:

        EXPORTED_NAMES - set of names exported via the platform
            module's namespace...

        GL, GLU, GLUT, GLE, GLES1, GLES2, GLES3, GLSC2, EGL, GLX - ctypes
            libraries, or None where this platform has no such library.
            A subclass normally overrides the ones it provides with a
            lazy_property, so each library is loaded on first use.

        DEFAULT_FUNCTION_TYPE - used as the default function
            type for functions unless overridden on a per-DLL
            basis with a "FunctionType" member

        GLUT_GUARD_CALLBACKS - if True, the GLUT wrappers
            will provide guarding wrappers to prevent GLUT
            errors with uninitialised GLUT.

        EXTENSIONS_USE_BASE_FUNCTIONS - if True, uses regular
            dll attribute-based lookup to retrieve extension
            function pointers.
    """

    EXPORTED_NAMES: ClassVar[list] = [
        'GetCurrentContext',
        'CurrentContextIsValid',
        'createBaseFunction',
        'createExtensionFunction',
        'copyBaseFunction',
        'getGLUTFontPointer',
        'nullFunction',
        'GLUT_GUARD_CALLBACKS',
    ]

    DEFAULT_FUNCTION_TYPE = None
    GLUT_GUARD_CALLBACKS = False
    EXTENSIONS_USE_BASE_FUNCTIONS = False

    # The libraries every platform defines.  None means the platform has no
    # such library.  The OpenGL.raw modules then still import, and each call
    # raises NullFunctionError naming the missing function.  Without the
    # attribute, `import OpenGL.GLES2` would raise an AttributeError on the
    # platform object, several frames away from the caller's code.
    GL = None
    GLU = None
    GLUT = None
    GLE = None
    GLES1 = None
    GLES2 = None
    GLES3 = None
    # OpenGL SC 2.0, the safety-critical profile.  No platform here loads it,
    # because it ships with conformant SC implementations rather than desktop
    # drivers.  Defined anyway, so `OpenGL.GLSC2` imports and its entry points
    # report themselves unavailable, like any other API a machine lacks.
    GLSC2 = None
    EGL = None
    GLX = None

    #: APIs that only one platform provides, mapped to the
    #: ``PYOPENGL_PLATFORM`` value that selects that platform.  Requesting one
    #: from another platform means the program did not select the platform, so
    #: the error names the setting.  See
    #: https://github.com/mcfletch/pyopengl/issues/129
    PLATFORM_SPECIFIC_APIS: ClassVar[dict] = {
        'OSMesa': 'osmesa',
    }

    def __getattr__(self, name):
        """Raise AttributeError naming the platform that provides ``name``.

        Called only when ordinary lookup fails, so a platform that provides
        the API returns it without reaching this method.

        The default ``AttributeError`` names a class the caller does not know
        (``'EGLPlatform' object has no attribute 'OSMesa'``) and looks like a
        PyOpenGL defect.  The message here names the ``PYOPENGL_PLATFORM``
        setting instead.  OSMesa users render on machines with no display, so
        the message gives them the setting directly.
        """
        platform = self.PLATFORM_SPECIFIC_APIS.get(name)
        if platform is None:
            raise AttributeError(
                '%r object has no attribute %r'
                % (self.__class__.__name__, name))
        raise AttributeError(
            '%r has no %s: it belongs to the %r platform, which this run did '
            'not select. Set PYOPENGL_PLATFORM=%s in the environment, or '
            'os.environ before the first `import OpenGL`, since the platform '
            'decides which library every entry point is loaded from.'
            % (self.__class__.__name__, name, platform, platform))

    def secondaryLibraries(self):
        """Libraries to search when an API's own does not export a name.

        Empty for a platform whose libraries each hold their own entry points.
        Windows overrides it: the pixel-format calls and SwapBuffers that a
        WGL program makes are GDI entry points, exported by gdi32 rather than
        opengl32.

        ``constructFunction`` here and the C dispatcher's resolver both call
        this, so both find the same entry points.
        """
        return ()

    def install(self, namespace):
        """Install this platform instance into the platform module"""
        for name in self.EXPORTED_NAMES:
            namespace[name] = getattr(self, name, None)
        namespace['PLATFORM'] = self
        return self

    def functionTypeFor(self, dll):
        """Given a DLL, determine appropriate function type..."""
        if hasattr(dll, 'FunctionType'):
            return dll.FunctionType
        else:
            return self.DEFAULT_FUNCTION_TYPE

    def errorChecking(self, func, dll, error_checker=None):
        """Add error checking to the function if appropriate"""
        from OpenGL import error

        if error_checker and _configflags.ERROR_CHECKING:
            # GLUT spec says error-checking is basically undefined...
            # there *may* be GL errors on GLUT calls that e.g. render
            # geometry, but that's all basically "maybe" stuff...
            func.errcheck = error_checker.glCheckError
        return func

    def wrapContextCheck(self, func, dll):
        """Wrap function with context-checking if appropriate

        ``CONTEXT_CHECKING`` applies to GL calls.  Three window-system APIs are
        exported from the GL library itself: ``libGL`` exports ``glX*``,
        ``opengl32`` exports ``wgl*``, and the OSMesa platform's GL library
        ``libOSMesa`` exports ``OSMesa*``.  A program calls these to create a
        context, so a context check on them would prevent creating the first
        context.  They are exempt.  EGL and CGL are separate libraries and
        need no exemption.
        """
        if (
            _configflags.CONTEXT_CHECKING
            and dll is self.GL
            and func.__name__
            not in (
                'glGetString',
                'glGetStringi',
                'glGetIntegerv',
            )
            and not func.__name__.startswith(('glX', 'wgl', 'OSMesa'))
        ):
            return _CheckContext(func, self.CurrentContextIsValid)
        return func

    def wrapLogging(self, func):
        """Wrap function with logging operations if appropriate"""
        return logs.logOnFailDec(logs.getLog('OpenGL.errors'))(func)

    def finalArgType(self, typ):
        """Retrieve a final type for arg-type"""
        if typ == ctypes.POINTER(None) and not getattr(typ, 'final', False):
            from OpenGL.arrays import ArrayDatatype

            return ArrayDatatype
        else:
            return typ

    def constructFunction(
        self,
        functionName,
        dll,
        resultType=ctypes.c_int,
        argTypes=(),
        doc=None,
        argNames=(),
        extension=None,
        deprecated=False,
        module=None,
        force_extension=False,
        force_base=False,
        error_checker=None,
    ):
        """Core operation to create a new base ctypes function

        A name is looked up where its declaration places it: a core entry
        point in the library, an extension entry point through the platform's
        ``getExtensionProcedure``.  ``force_extension`` and ``force_base``
        override that choice for platforms whose libraries split entry points
        differently from the declarations.  See
        :class:`SplitEntryPointPlatform`, which tries each route in turn.
        ``force_base`` also skips the extension check, because a name the
        library exports is present whether or not the extension that
        re-specified it is advertised.

        raises AttributeError if can't find the procedure...
        """
        # Core/version modules name themselves e.g. GLES2_VERSION_GLES2_2_0 or
        # GLES2_ES_VERSION_3_2, so the 'VERSION' token is not always at index 1.
        from OpenGL.error import inside_begin_block

        is_core = (not extension) or 'VERSION' in extension.split('_')
        # The extension check is skipped inside a glBegin block, where the
        # extension string cannot be read.
        # _dispatch.support._extension_gate_passes applies the same rule in
        # the compiled dispatch layer.  The check is also
        # skipped for force_base, which marks a name the library exports.  An
        # extension that re-specifies a GL 1.1 entry point changes its
        # arguments, and the entry point exists either way.
        if (
            (not is_core)
            and not force_base
            and not inside_begin_block()
            and not self.checkExtension(extension)
        ):
            # If a core version declares the same name, the library exports it
            # and the extension only re-specified its arguments.  The lookup
            # then goes to the library.  The compiled layer does the same,
            # using each command's ``alternates``.
            #
            # This applies only to names a core version declares.  macOS
            # exports every entry point its framework implements, whether or
            # not the current context supports it.  Looking up any exported
            # name would report an unadvertised extension as present on macOS.
            if _also_core(functionName, module):
                force_base = True
            else:
                raise AttributeError("""Extension not available""")
        argTypes = [self.finalArgType(t) for t in argTypes]

        if not force_base and (
            force_extension
            or ((not is_core) and (not self.EXTENSIONS_USE_BASE_FUNCTIONS))
        ):
            # what about the VERSION values???
            pointer = self.getExtensionProcedure(as_8_bit(functionName))
            if pointer:
                func = self.functionTypeFor(dll)(resultType, *argTypes)(pointer)
            else:
                raise AttributeError(
                    """Extension %r available, but no pointer for function %r"""
                    % (extension, functionName)
                )
        else:
            func = ctypesloader.buildFunction(
                self.functionTypeFor(dll)(resultType, *argTypes),
                functionName,
                dll,
            )
        func.__doc__ = doc
        func.argNames = list(argNames or ())
        func.__name__ = functionName
        func.DLL = dll
        func.extension = extension
        func.deprecated = deprecated
        func = self.wrapLogging(
            self.wrapContextCheck(
                self.errorChecking(func, dll, error_checker=error_checker),
                dll,
            )
        )
        if MODULE_ANNOTATIONS:
            if not module:
                module = _find_module()
            if module:
                func.__module__ = module
        return func

    def createBaseFunction(
        self,
        functionName,
        dll,
        resultType=ctypes.c_int,
        argTypes=(),
        doc=None,
        argNames=(),
        extension=None,
        deprecated=False,
        module=None,
        error_checker=None,
    ):
        """Create a base function for given name

        Normally you can just use the dll.name hook to get the object,
        but we want to be able to create different bindings for the
        same function, so we do the work manually here to produce a
        base function from a DLL.
        """
        from OpenGL import wrapper

        result = None
        try:
            if _configflags.FORWARD_COMPATIBLE_ONLY and dll is self.GL and deprecated:
                result = self.nullFunction(
                    functionName,
                    dll=dll,
                    resultType=resultType,
                    argTypes=argTypes,
                    doc=doc,
                    argNames=argNames,
                    extension=extension,
                    deprecated=deprecated,
                    error_checker=error_checker,
                    module=module,
                )
            else:
                result = self.constructFunction(
                    functionName,
                    dll,
                    resultType=resultType,
                    argTypes=argTypes,
                    doc=doc,
                    argNames=argNames,
                    extension=extension,
                    error_checker=error_checker,
                    module=module,
                )
        except AttributeError as err:
            result = self.nullFunction(
                functionName,
                dll=dll,
                resultType=resultType,
                argTypes=argTypes,
                doc=doc,
                argNames=argNames,
                extension=extension,
                error_checker=error_checker,
                module=module,
            )
        if MODULE_ANNOTATIONS:
            if not module:
                module = _find_module()
            if module:
                result.__module__ = module
        return result

    def checkExtension(self, name):
        """Check whether the given extension is supported by current context"""
        #        if not name or name in ('GL_VERSION_GL_1_0', 'GL_VERSION_GL_1_1'):
        #            return True
        #        if name.startswith( 'EGL_' ) or name.startswith( 'GLX_' ) or name.startswith( 'WGL_' ):
        #            # we can't check these extensions, have to rely on the function resolution
        #            return True
        if not name:
            return True
        # The GLES raw modules name their extensions e.g. 'GLES2_OES_foo', but the
        # GL extension string reported by the driver is 'GL_OES_foo'.  Normalise so
        # the lookup matches (desktop modules already use the 'GL_' form).
        if name.startswith('GLES'):
            tail = name.split('_', 1)
            if len(tail) == 2:
                name = 'GL_' + tail[1]
        context = self.GetCurrentContext()
        if context:
            from OpenGL import contextdata

            set = contextdata.getValue('extensions', context=context)
            if set is None:
                set = {}
                contextdata.setValue('extensions', set, context=context, weak=False)
            current = set.get(name)
            if current is None:
                from OpenGL import extensions

                result = extensions.ExtensionQuerier.hasExtension(name)
                set[name] = result
                return result
            return current
        else:
            from OpenGL import extensions

            return extensions.ExtensionQuerier.hasExtension(name)

    createExtensionFunction = createBaseFunction

    def copyBaseFunction(self, original):
        """Create a new base function based on an already-created function

        This is normally used to provide type-specific convenience versions of
        a definition created by the automated generator.
        """
        from OpenGL import wrapper, error

        if isinstance(original, _NullFunctionPointer):
            return self.nullFunction(
                original.__name__,
                original.DLL,
                resultType=original.restype,
                argTypes=original.argtypes,
                doc=original.__doc__,
                argNames=original.argNames,
                extension=original.extension,
                deprecated=original.deprecated,
                error_checker=original.error_checker,
                module=original.module,
            )
        elif hasattr(original, 'originalFunction'):
            original = original.originalFunction
        return self.createBaseFunction(
            original.__name__,
            original.DLL,
            resultType=original.restype,
            argTypes=original.argtypes,
            doc=original.__doc__,
            argNames=original.argNames,
            extension=original.extension,
            deprecated=original.deprecated,
            error_checker=original.errcheck,
        )

    def nullFunction(
        self,
        functionName,
        dll,
        resultType=ctypes.c_int,
        argTypes=(),
        doc=None,
        argNames=(),
        extension=None,
        deprecated=False,
        module=None,
        error_checker=None,
        force_extension=False,
    ):
        """Construct a "null" function pointer"""
        if deprecated:
            base = _DeprecatedFunctionPointer
        else:
            base = _NullFunctionPointer
        cls = type(
            functionName,
            (base,),
            {
                '__doc__': doc,
                'deprecated': deprecated,
            },
        )
        if MODULE_ANNOTATIONS:
            if not module:
                module = _find_module()
            if module:
                cls.__module__ = module
        return cls(
            functionName,
            dll,
            resultType,
            argTypes,
            argNames,
            extension=extension,
            doc=doc,
            error_checker=error_checker,
            force_extension=force_extension,
            module=module,
        )

    def GetCurrentContext(self):
        """Retrieve opaque pointer for the current context"""
        raise NotImplementedError(
            """Platform does not define a GetCurrentContext function"""
        )

    def releaseCurrentContext(self):
        """Release this thread's current GL context; True if one was released

        A thread has at most one current context, and a platform's GL binding
        APIs do not track each other.  On Linux, making an EGL context current
        while a GLX context is current fails with ``EGL_BAD_ACCESS``.  The
        reverse is an X ``BadAccess`` on ``X_GLXMakeCurrent``, and Xlib's
        default error handler exits the process.

        A program with two GL views can hit this, for example two windowing
        toolkits in one process.  It calls this method before making its own
        context current.  The call is safe when no context is current, so a
        caller can always make it.

        A platform with one binding API and no way to release returns False.
        """
        return False

    def currentContextAddress(self):
        """The address of the platform's current-context function, or None.

        The C dispatch layer calls the function directly to choose which
        context's entry-point table a thread uses, so it needs the address
        rather than the ctypes callable.  With None, the layer uses a single
        table, which is correct for a process with only one context.
        """
        try:
            return ctypes.cast(self.GetCurrentContext, ctypes.c_void_p).value
        except (ctypes.ArgumentError, TypeError):
            return None

    def getGLUTFontPointer(self, constant):
        """Retrieve a GLUT font pointer for this platform"""
        raise NotImplementedError(
            """Platform does not define a GLUT font retrieval function"""
        )

    # names that are normally just references to other items...
    @lazy_property
    def CurrentContextIsValid(self):
        return self.GetCurrentContext

    @lazy_property
    def OpenGL(self):
        return self.GL


class SplitEntryPointPlatform(BasePlatform):
    """A platform holding its entry points in more than one place

    Windows' ``opengl32`` exports only the GL 1.1 set.  ``wglGetProcAddress``
    returns everything above GL 1.1 and NULL for the 1.1 set.  Mesa's Windows
    ``osmesa`` library has the same export list, with
    ``OSMesaGetProcAddress`` for the rest.  Neither split follows the
    declarations.  ``glVertexAttribPointer`` is declared by a core version,
    and the same Mesa built for Linux exports it directly.  Each route is
    therefore tried in turn.

    Only a platform whose procedure lookup returns NULL for unknown names
    belongs here.  ``glXGetProcAddressARB`` under libglvnd returns a dispatch
    stub for any name, including names no API defines.  A Linux platform
    using this class would report every undefined entry point as present.
    """

    def entryPointRoutes(self, dll):
        """The lookups to try for a name, in order

        Each is the keyword arguments for one call to
        :meth:`BasePlatform.constructFunction`: first the library the
        declaration names, then the platform's procedure lookup.
        """
        return (
            dict(dll=dll),
            dict(dll=dll, force_extension=True),
        )

    def constructFunction(self, functionName, dll, force_extension=False, **named):
        """The function from the first of :meth:`entryPointRoutes` that finds it

        If the last route also fails, its ``AttributeError`` propagates, and
        :meth:`BasePlatform.createBaseFunction` turns it into a null function.

        Every route is tried, so a caller's ``force_extension`` cannot change
        the result and is not passed on.
        """
        routes = self.entryPointRoutes(dll)
        for index, route in enumerate(routes):
            try:
                return super().constructFunction(
                    functionName, **dict(named, **route)
                )
            except AttributeError:
                if index == len(routes) - 1:
                    raise


class _NullFunctionPointer(object):
    """Function-pointer-like object for undefined functions"""

    def __init__(
        self,
        name,
        dll,
        resultType,
        argTypes,
        argNames,
        extension=None,
        doc=None,
        deprecated=False,
        error_checker=None,
        force_extension=None,
        module=None,
    ):
        from OpenGL import error

        self.__name__ = name
        self.DLL = dll
        self.argNames = argNames
        self.argtypes = argTypes
        self.errcheck = None
        self.restype = resultType
        self.extension = extension
        self.doc = doc
        self.deprecated = deprecated
        self.error_checker = error_checker
        self.force_extension = force_extension
        #: The generated module this was declared in, which identifies the
        #: API.  Stored because :meth:`load` calls ``constructFunction`` again,
        #: and the result depends on the API.
        self.module = module

    resolved = False

    def __nonzero__(self):
        """Whether calling this entry point will reach the library

        :class:`OpenGL.error.NullFunctionError` tells callers to make this
        check, so it attempts resolution.  An entry point the library exports
        is present even if nothing has called it yet.  Returning False for it
        would make the caller skip work the driver supports.

        A False result is not cached.  An entry point that needs a current
        context resolves once a context is current.
        """
        if not self.resolved:
            self.load()
        return self.resolved

    __bool__ = __nonzero__

    def load(self):
        """Attempt to load the function again, presumably with a context this time"""
        try:
            from OpenGL import platform
        except ImportError:
            if log:
                log.info('Platform import failed (likely during shutdown)')
            return None
        try:
            func = platform.PLATFORM.constructFunction(
                self.__name__,
                self.DLL,
                resultType=self.restype,
                argTypes=self.argtypes,
                doc=self.doc,
                argNames=self.argNames,
                extension=self.extension,
                error_checker=self.error_checker,
                force_extension=self.force_extension,
                module=self.module,
            )
        except AttributeError as err:
            return None
        else:
            # now short-circuit so that we don't need to check again...
            self.__class__.__call__ = staticmethod(func.__call__)
            self.resolved = True
            return func
        return None

    def __call__(self, *args, **named):
        if self.load():
            return self(*args, **named)
        else:
            try:
                from OpenGL import error
            except ImportError as err:
                # Python interpreter is shutting down...
                pass
            else:
                raise error.NullFunctionError(
                    undefined_function_message(
                        self.__name__, self.DLL, _context_is_current()
                    )
                )


class _DeprecatedFunctionPointer(_NullFunctionPointer):
    deprecated = True

    def __nonzero__(self):
        """Always False, whatever the driver exports

        Entry points become this class under ``FORWARD_COMPATIBLE_ONLY``,
        which refuses every call to them, so no resolution is attempted.
        """
        return False
    __bool__ = __nonzero__

    def __call__(self, *args, **named):
        from OpenGL import error

        raise error.NullFunctionError(
            """Attempt to call a deprecated function %s while OpenGL in FORWARD_COMPATIBLE_ONLY mode.  Set OpenGL.FORWARD_COMPATIBLE_ONLY to False to use legacy entry points"""
            % (self.__name__,)
        )
