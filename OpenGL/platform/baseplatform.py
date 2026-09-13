"""Base class for platform implementations
"""

import ctypes
from OpenGL.platform import ctypesloader
from OpenGL._bytes import as_8_bit
import sys, logging
from OpenGL import _configflags
from OpenGL import logs, MODULE_ANNOTATIONS

log = logging.getLogger(__name__)

#: Which library an entry point lives in, read from the prefix of its name.
#:
#: Longest first, because ``glutInit`` also begins with ``glu``.
#:
#: The prefix is the API's own naming rather than a guess -- the registry and
#: the SGI headers assign it -- and where the library could not be loaded at
#: all it is the only thing left to read.  The platform answers ``None`` for
#: such a library, so every declaration in the module is built against
#: ``None`` and there is no object to ask which one it was.
ENTRY_POINT_PREFIXES = (
    ('glut', 'GLUT'),
    ('glu', 'GLU'),
    ('gle', 'GLE'),
    ('egl', 'EGL'),
    ('wgl', 'GL'),
    ('glX', 'GL'),
    ('gl', 'GL'),
)

#: Where to get a library this machine does not have.
#:
#: Per platform, because the answer differs and the reader has one machine in
#: front of them -- #59 was on Arch and then on CentOS, and #54's answer, when
#: it came thirteen months later, was a Debian package name.
#:
#: GL is deliberately absent: no OpenGL library at all means no graphics
#: driver, which is a different conversation from a package that was not
#: installed, and a package name would be the wrong advice.
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


#: Why an entry point does not resolve when there is no context.
#:
#: Shared with :func:`OpenGL.extensions.alternate`, which reports the same
#: situation for a call that has several possible names and found none of
#: them -- the framebuffer-object entry points among them.
NO_CONTEXT_EXPLANATION = (
    'no OpenGL context is current, and every entry point above GL 1.1 is '
    'resolved through the context -- so this says the call came before a '
    'context was created rather than that the driver lacks it. Create a '
    'context first, through GLUT, GLFW, pygame, Qt, EGL or whatever your '
    'program uses'
)


def library_for_entry_point(name):
    """The library ``name`` belongs to, or None where the prefix says nothing.

    See :data:`ENTRY_POINT_PREFIXES` for why the name is what answers this.
    """
    for prefix, library in ENTRY_POINT_PREFIXES:
        if name.startswith(prefix):
            return library
    return None


def undefined_function_message(name, dll, has_context=None):
    """Why ``name`` cannot be called, in terms the caller can act on.

    Three situations reach here and they want different answers.

    A ``dll`` of ``None`` means the library itself was not found, so every
    entry point in it is undefined and there is one thing to do about it.

    A library that loaded, with no context current, means the entry point
    could not be *resolved* rather than that it is absent: above GL 1.1 an
    address comes from the context, so every such name is undefined until
    there is one.  This is the usual way to meet the error on Windows, where
    ``wglGetProcAddress`` needs a current context; GLX answers without one,
    so it is rarer on Linux.  It is the case the old message described least
    well, naming a driver problem for what is an ordering problem in the
    caller's own program.

    A library that loaded with a context current, and still no entry point, is
    a driver too old for it or an extension this machine does not have. There
    is nothing to install.

    ``has_context`` is ``None`` where it could not be determined, which reads
    as the third case rather than guessing.

    All three end by naming ``bool(name)``, which is the check this error has
    always pointed at and what a caller already handling it looks for.
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
    """Whether a GL context is current, or None where that cannot be asked.

    Only ever called while building an error message, so the cost of asking
    the driver is paid on a path that is already failing -- and any platform
    that cannot answer says so rather than turning one error into another.
    """
    try:
        from OpenGL import platform

        return bool(platform.PLATFORM.GetCurrentContext())
    except Exception:
        return None


class lazy_property(object):
    """An attribute worked out when it is first read, then cached on the instance

    The platform objects describe libraries, and finding one means loading it.
    Doing that for every attribute at import would load libraries the program
    never asks about.
    """

    def __init__(self, function):
        self.fget = function
        self.__name__ = function.__name__
        self.__doc__ = function.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:
            # Read from the class, where there is no instance to work anything
            # out for.  Answering with the descriptor is what every other
            # descriptor in Python does, and it is how help(), inspect and a
            # documentation build ask a class what it has without owning one.
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

    ``module`` is the generated module the declaration came from, which is
    what says the API to ask about.  False where there is none to ask -- a
    caller building a binding by hand, or one of the hand-maintained APIs
    (GLU, GLUT, GLE) that no table describes.
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

        EXPORTED_NAMES -- set of names exported via the platform
            module's namespace...

        GL, GLU, GLUT, GLE, GLES1, GLES2, GLES3, GLSC2, EGL, GLX -- ctypes
            libraries, or None where this platform has no such library.
            A subclass normally overrides the ones it can provide with a
            lazy_property, so that a library is only loaded once something
            asks for it.

        DEFAULT_FUNCTION_TYPE -- used as the default function
            type for functions unless overridden on a per-DLL
            basis with a "FunctionType" member

        GLUT_GUARD_CALLBACKS -- if True, the GLUT wrappers
            will provide guarding wrappers to prevent GLUT
            errors with uninitialised GLUT.

        EXTENSIONS_USE_BASE_FUNCTIONS -- if True, uses regular
            dll attribute-based lookup to retrieve extension
            function pointers.
    """

    EXPORTED_NAMES = [
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

    # The libraries every platform is asked about.  None means "this platform
    # has no such library", which the OpenGL.raw modules read as "no entry
    # points here": the namespace still imports, and calling into it raises
    # NullFunctionError naming the function that is missing.  Leaving one
    # undefined instead turns `import OpenGL.GLES2` into an AttributeError
    # against the platform object, several frames from anything the caller
    # wrote.
    GL = None
    GLU = None
    GLUT = None
    GLE = None
    GLES1 = None
    GLES2 = None
    GLES3 = None
    # OpenGL SC 2.0, the safety-critical profile.  No platform here loads one:
    # it ships with a conformant SC implementation rather than with a desktop
    # driver.  Named all the same, so `OpenGL.GLSC2` imports and its entry
    # points report themselves unavailable, which is what every other API a
    # machine lacks does.
    GLSC2 = None
    EGL = None
    GLX = None

    #: APIs that belong to one platform rather than being a library every
    #: platform may or may not have, mapped to the ``PYOPENGL_PLATFORM`` value
    #: that selects it.  Asking any other platform for one of these is not a
    #: machine missing a library, it is a program that has not said which
    #: platform it wants -- and the answer is a setting, so the refusal names
    #: it.  See https://github.com/mcfletch/pyopengl/issues/129
    PLATFORM_SPECIFIC_APIS = {
        'OSMesa': 'osmesa',
    }

    def __getattr__(self, name):
        """Say how to reach an API that belongs to a platform this is not.

        Reached only when ordinary lookup has failed, so a platform that
        provides the API answers with it and never arrives here.

        The default ``AttributeError`` names an attribute of a class the
        caller has never heard of -- ``'EGLPlatform' object has no attribute
        'OSMesa'`` -- which reads as a defect in PyOpenGL rather than as a
        choice they have not made.  Whoever meets this one can least afford
        that: OSMesa is how a machine with no display renders, so by
        construction they cannot see what their session is.
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
        Windows is the exception and says so for itself: the pixel-format calls
        and SwapBuffers that a WGL program makes are GDI entry points rather
        than OpenGL ones, and live in gdi32 instead of opengl32.

        Both ways of binding a function ask this -- ``constructFunction`` here
        and the dispatcher's own resolver -- so that an entry point one of them
        can reach is not missing from the other.
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

        ``CONTEXT_CHECKING`` is a question about *GL*, and two display APIs
        ship in the GL library rather than in one of their own: ``libGL``
        exports ``glX*`` and ``opengl32`` exports ``wgl*``.  Their calls are
        what a program makes to *get* a context, so a guard on one asks for a
        context before there can be one and leaves no way to make the first.
        EGL and CGL need no exemption, being libraries of their own.
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
            and not func.__name__.startswith(('glX', 'wgl'))
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

        A name is normally looked for where its declaration says it lives: a
        core entry point in the library, an extension one through the
        platform's ``getExtensionProcedure``.  ``force_extension`` and
        ``force_base`` override that either way, for a platform whose loader
        does not divide them where the declarations do -- see
        :class:`OpenGL.platform.win32.Win32Platform`, which tries both.
        ``force_base`` also stands the extension gate aside, since a name the
        library exports is present whether or not the extension that
        re-specified it is advertised.

        raises AttributeError if can't find the procedure...
        """
        # Core/version modules name themselves e.g. GLES2_VERSION_GLES2_2_0 or
        # GLES2_ES_VERSION_3_2 -- the 'VERSION' token is not always at index 1.
        from OpenGL.error import inside_begin_block

        is_core = (not extension) or 'VERSION' in extension.split('_')
        # The gate stands aside inside a glBegin block, where the extension
        # string cannot be read -- see _dispatch.support._extension_gate_passes,
        # which states the same rule for the compiled dispatch layer.  And for
        # force_base, which says the name is one the library exports: what an
        # extension re-specifies about a GL 1.1 entry point is which arguments
        # it takes, and the entry point is there either way.
        if (
            (not is_core)
            and not force_base
            and not inside_begin_block()
            and not self.checkExtension(extension)
        ):
            # A core version declaring the same name means the library exports
            # it, and what the extension re-specified is which arguments it
            # takes rather than whether it exists.  So the gate stands aside
            # and the library answers -- which is what the compiled layer does
            # with the same fact, held as each command's ``alternates``.
            #
            # Only for such a name, and not for whatever the library happens
            # to export: macOS exports every entry point its framework
            # implements whether or not the current context does, so answering
            # from the library alone would report an unadvertised extension as
            # present there, which is the question the gate exists to answer.
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
        """Let go of the GL context this thread holds; answer whether there was one

        **A thread may have one current context, and a platform's GL binding
        APIs do not know about each other.**  On Linux, asking EGL to make a
        context current while GLX holds the thread is ``EGL_BAD_ACCESS``, and
        the reverse is an X ``BadAccess`` on ``X_GLXMakeCurrent`` -- which
        Xlib's default error handler turns into a process exit rather than an
        exception anything can catch.

        So a program with two GL views in it -- two windowing toolkits in one
        process, an engine's suite exercising one backend while a helper opens
        a window through another -- needs to be able to say "let go" before it
        takes the thread.  Safe to call when nothing is current, which is why a
        caller can simply always call it.

        A platform with one binding API and no way to release answers False.
        """
        return False

    def currentContextAddress(self):
        """The address of the platform's current-context function, or None.

        The C dispatch layer calls it directly to decide which context's
        entry-point table a thread dispatches through, so it needs the address
        rather than the ctypes callable.  Returning None is not a failure: the
        layer then dispatches through a single table, which is correct for a
        process that only ever has one context current.
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
        #: The generated module this was declared in, which is what says the
        #: API a later resolution is for.  Kept because :meth:`load` runs
        #: ``constructFunction`` again, and the answer differs by API.
        self.module = module

    resolved = False

    def __nonzero__(self):
        """Whether calling this entry point will reach the library

        This is the check :class:`OpenGL.error.NullFunctionError` names, so it
        has to answer for the call rather than for the bookkeeping: an entry
        point the library exports but nothing has called yet is present, and
        saying otherwise sends the caller past work the driver would have done.
        Trying to resolve it is the only thing that can tell them apart.

        A no is about the moment it was asked -- an entry point that needs a
        current context resolves once there is one -- so it is not remembered.
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
        """Always absent: the call is refused whatever the driver exports

        ``FORWARD_COMPATIBLE_ONLY`` is what puts an entry point here, and it
        refuses the call rather than resolving it, so resolving it is not the
        question.
        """
        return False
    __bool__ = __nonzero__

    def __call__(self, *args, **named):
        from OpenGL import error

        raise error.NullFunctionError(
            """Attempt to call a deprecated function %s while OpenGL in FORWARD_COMPATIBLE_ONLY mode.  Set OpenGL.FORWARD_COMPATIBLE_ONLY to False to use legacy entry points"""
            % (self.__name__,)
        )
