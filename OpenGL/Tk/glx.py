"""An OpenGL context on a Tk widget's X11 window.

Tk gives out the X window id (``winfo_id()``); GLX makes a context against one.
Two questions are asked of the driver, and :func:`configAttributes` and
:func:`contextAttributes` are what a
:class:`~OpenGL.Tk.attributes.ContextAttributes` becomes for each:

* which framebuffer configuration to use (``glXChooseFBConfig``), and
* which context to make on it (``glXCreateContextAttribsARB``, where the
  profile and version come from).

**The window has to already have the visual the configuration wants.**  X ties
a window to a visual when it is created and a context can only be made current
on a window whose visual matches its configuration, so the configuration is
chosen from among those matching the visual Tk already gave the widget rather
than from the whole list.  A widget cannot be re-made with another visual after
the fact, which is why nothing here tries.
"""

from __future__ import annotations

import ctypes
import logging
from typing import Any, List, Optional

from OpenGL import GL, GLX
from OpenGL.GLX.ARB import create_context as _create_context
from OpenGL.GLX.ARB import create_context_profile as _create_context_profile
from OpenGL.error import end_abandoned_block
from OpenGL.platform import ctypesloader
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.context import gone, nowCurrent
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

# The constants and entry points in these two arrive from PyOpenGL's generated
# declaration tables as the module is imported, so a checker reading the source
# finds none of them by name.  Aliased through Any rather than annotated one at
# a time: there is nothing a checker could usefully say about a table it cannot
# see, and forty suppressions would bury the errors it *can* find here.
create_context: Any = _create_context
create_context_profile: Any = _create_context_profile

__all__ = ['GLXContext', 'configAttributes', 'contextAttributes']


def configAttributes(attributes: ContextAttributes) -> List[int]:
    """The ``glXChooseFBConfig`` attribute list a request asks for

    Terminated with ``GL_NONE``, as that call requires.  What is *not* in the
    list matters: an attribute nobody asked for is left out rather than asked
    for as zero, because ``glXChooseFBConfig`` treats a named attribute as a
    minimum and a driver with no such configuration then matches nothing.
    """
    wanted = [
        GLX.GLX_X_RENDERABLE, 1,
        GLX.GLX_DRAWABLE_TYPE, GLX.GLX_WINDOW_BIT,
        GLX.GLX_RENDER_TYPE, GLX.GLX_RGBA_BIT,
        GLX.GLX_X_VISUAL_TYPE, GLX.GLX_TRUE_COLOR,
        GLX.GLX_RED_SIZE, attributes.redSize,
        GLX.GLX_GREEN_SIZE, attributes.greenSize,
        GLX.GLX_BLUE_SIZE, attributes.blueSize,
        GLX.GLX_ALPHA_SIZE, attributes.alphaSize,
        GLX.GLX_DEPTH_SIZE, attributes.depthSize,
        GLX.GLX_STENCIL_SIZE, attributes.stencilSize,
        GLX.GLX_DOUBLEBUFFER, 1 if attributes.doubleBuffer else 0,
    ]
    if attributes.samples > 0:
        wanted += [GLX.GLX_SAMPLE_BUFFERS, 1, GLX.GLX_SAMPLES,
                   attributes.samples]
    if attributes.stereo:
        wanted += [GLX.GLX_STEREO, 1]
    return wanted + [GL.GL_NONE]


def contextAttributes(attributes: ContextAttributes) -> List[int]:
    """The ``glXCreateContextAttribsARB`` attribute list a request asks for

    Terminated with 0.  A ``legacy`` request has nothing to say here -- no
    version and no profile -- and is created through ``glXCreateNewContext``
    instead; see :meth:`GLXContext._create`.
    """
    wanted: List[int] = []
    if attributes.version:
        wanted += [
            create_context.GLX_CONTEXT_MAJOR_VERSION_ARB, attributes.version[0],
            create_context.GLX_CONTEXT_MINOR_VERSION_ARB, attributes.version[1],
        ]
    if attributes.profileApplies():
        wanted += [
            create_context_profile.GLX_CONTEXT_PROFILE_MASK_ARB,
            create_context_profile.GLX_CONTEXT_CORE_PROFILE_BIT_ARB
            if attributes.profile == 'core'
            else create_context_profile.GLX_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB,
        ]
    flags = 0
    if attributes.forwardCompatibleApplies():
        flags |= create_context.GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
    if attributes.debug:
        flags |= create_context.GLX_CONTEXT_DEBUG_BIT_ARB
    if flags:
        wanted += [create_context.GLX_CONTEXT_FLAGS_ARB, flags]
    return wanted + [0]


class XErrorEvent(ctypes.Structure):
    """The X error report an error handler is handed

    Only as far as the fields this reads; the rest of the structure is longer
    and nothing here looks past ``resourceid``.
    """

    _fields_ = [
        ('type', ctypes.c_int),
        ('display', ctypes.c_void_p),
        ('serial', ctypes.c_ulong),
        ('error_code', ctypes.c_ubyte),
        ('request_code', ctypes.c_ubyte),
        ('minor_code', ctypes.c_ubyte),
        ('resourceid', ctypes.c_ulong),
    ]


#: The signature ``XSetErrorHandler`` takes.  Kept at module scope because a
#: ctypes callback must outlive every call that could reach it, and one built
#: inside a function would be collected the moment it returned.
ERROR_HANDLER = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(XErrorEvent))


def _x11() -> Any:
    """The Xlib entry points this module calls, with their signatures set"""
    library = ctypesloader.loadLibrary(ctypes.cdll, 'X11')
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]
    library.XOpenDisplay.restype = ctypes.POINTER(GLX.Display)
    library.XCloseDisplay.argtypes = [ctypes.POINTER(GLX.Display)]
    library.XDefaultScreen.argtypes = [ctypes.POINTER(GLX.Display)]
    library.XDefaultScreen.restype = ctypes.c_int
    library.XFree.argtypes = [ctypes.c_void_p]
    library.XSync.argtypes = [ctypes.POINTER(GLX.Display), ctypes.c_int]
    library.XSetErrorHandler.argtypes = [ERROR_HANDLER]
    library.XSetErrorHandler.restype = ERROR_HANDLER
    return library


class collectedXErrors(object):
    """Catch X's errors for the length of the block instead of dying of them

    **Xlib's default error handler prints to stderr and calls ``exit()``.**  A
    library cannot leave that in place around a request the server may refuse:
    asking for a GL version a driver will not give would end the application
    rather than raise something it could catch and answer.

    X reports errors asynchronously, so the request has to be flushed and the
    reply read before the block ends -- :meth:`sync` is that, and it is called
    on the way out.

    ``XSetErrorHandler`` is process-wide, so this is not thread-safe; there is
    no per-display handler in Xlib to be safe with.
    """

    def __init__(self, library: Any, display: Any) -> None:
        self.library = library
        self.display = display
        self.errors: List[str] = []
        self._previous = None
        self._handler = ERROR_HANDLER(self._collect)

    def _collect(self, display: Any, event: Any) -> int:
        report = event.contents
        self.errors.append(
            'X error %d on request %d.%d'
            % (report.error_code, report.request_code, report.minor_code))
        return 0

    def sync(self) -> None:
        """Flush what has been asked and read whatever the server said"""
        self.library.XSync(self.display, False)

    def __enter__(self) -> "collectedXErrors":
        self._previous = self.library.XSetErrorHandler(self._handler)
        return self

    def __exit__(self, *exception: object) -> None:
        try:
            self.sync()
        finally:
            self.library.XSetErrorHandler(self._previous)


class GLXContext(object):
    """A GLX context bound to the X window a Tk widget owns

    Built by :func:`OpenGL.Tk.context.createContext`; a caller reaches it as
    ``frame.context``.

    Attributes:
        handle -- the ``GLXContext`` the driver made, which is what PyOpenGL's
            per-context dispatch tables are keyed by
        display -- the ``Display*`` this context's connection uses
        drawable -- the X window id it draws into
    """

    handle = None
    display = None
    drawable = None

    def __init__(self, widget: Any, attributes: ContextAttributes) -> None:
        self.attributes = attributes
        self._x11 = _x11()
        # A connection of this module's own rather than Tk's.  Tk does not hand
        # its Display* out, and a second connection to the same server draws
        # into the same window perfectly well -- it is the window id that
        # identifies the target, not the connection that asked about it.
        self.display = self._x11.XOpenDisplay(
            widget.winfo_screen().encode('utf-8'))
        if not self.display:
            raise TkContextError(
                'Could not open the X display %r that Tk is using'
                % (widget.winfo_screen(),))
        self.drawable = int(widget.winfo_id())
        try:
            self.config = self._chooseConfig(widget)
            self.handle = self._create(attributes)
        except Exception:
            self._closeDisplay()
            raise

    ### creation
    def _chooseConfig(self, widget: Any) -> Any:
        """The framebuffer configuration matching both the request and Tk

        A context is only ever current on a window whose visual its
        configuration was chosen for, and Tk chose the widget's visual when it
        made the window, so the search is narrowed to configurations on that
        visual.  Where none matches -- Tk's default visual has no depth buffer
        on some servers -- the best of the rest is taken and the difference is
        logged, since a context on the wrong visual is a ``BadMatch`` and no
        other explanation.
        """
        screen = self._x11.XDefaultScreen(self.display)
        wanted = configAttributes(self.attributes)
        count = GL.GLint(0)
        configs = GLX.glXChooseFBConfig(
            self.display, screen,
            (GL.GLint * len(wanted))(*wanted), count,
        )
        if not configs or not count.value:
            raise TkContextError(
                'No framebuffer configuration matches %s'
                % (self.attributes.describe(),))
        try:
            visual = int(widget.winfo_visualid(), 16)
            for index in range(count.value):
                if self._visualOf(configs[index]) == visual:
                    return self._keep(configs[index])
            log.debug(
                'no framebuffer configuration on Tk\'s visual 0x%x; '
                'using the first of %d that matched the request instead',
                visual, count.value,
            )
            return self._keep(configs[0])
        finally:
            self._x11.XFree(configs)

    @staticmethod
    def _keep(config: Any) -> Any:
        """A copy of a configuration handle that outlives the array it was in

        Indexing a ctypes pointer array gives a **view onto that memory**, not
        a copy of the value: after ``XFree`` releases the array, reading the
        handle again gives whatever is in the freed block, and the driver
        answers ``GLXBadFBConfig`` -- fatally, since Xlib's default error
        handler exits.  ``cast`` builds an object holding the address itself.
        """
        return ctypes.cast(config, type(config))

    def _visualOf(self, config: Any) -> Optional[int]:
        """The X visual id a framebuffer configuration draws on, or None"""
        value = GL.GLint(0)
        if GLX.glXGetFBConfigAttrib(self.display, config, GLX.GLX_VISUAL_ID,
                                    value):
            return None                 # the config has no visual (a pbuffer)
        return int(value.value)

    def _create(self, attributes: ContextAttributes) -> Any:
        """Make the context, saying why if the driver will not

        ``ARB_create_context`` is what a version or a profile is asked through,
        and a driver without it can only answer the older call -- which is
        also the only thing a ``legacy`` request wants.
        """
        share = getattr(attributes.share, 'handle', attributes.share) or None
        legacy = attributes.version is None and attributes.profile == 'legacy'
        if not legacy and not create_context.glXCreateContextAttribsARB:
            raise TkContextError(
                'This driver has no GLX_ARB_create_context, so it cannot be '
                'asked for %s; ask for profile="legacy" to take whatever it '
                'offers' % (attributes.describe(),))
        with collectedXErrors(self._x11, self.display) as errors:
            if legacy:
                handle = GLX.glXCreateNewContext(
                    self.display, self.config, GLX.GLX_RGBA_TYPE, share, True)
            else:
                wanted = contextAttributes(attributes)
                handle = create_context.glXCreateContextAttribsARB(
                    self.display, self.config, share, True,
                    (ctypes.c_int * len(wanted))(*wanted),
                )
            # X reports a refusal asynchronously, so the request has to be
            # flushed and the reply read before the answer means anything.
            errors.sync()
        if errors.errors or not handle:
            raise TkContextError(
                'The driver would not create a context for %s%s'
                % (attributes.describe(),
                   ' (%s)' % ('; '.join(errors.errors),) if errors.errors
                   else ''))
        return handle

    ### the context protocol
    def makeCurrent(self) -> bool:
        """Draw into this widget from now on; False if the driver refused

        Whatever held the thread is let go of first.  A thread may have one
        current context, and EGL and GLX do not know about each other: asking
        GLX for the thread while an EGL context holds it is an X ``BadAccess``,
        which Xlib's default error handler turns into a process exit rather
        than something a caller could answer.  That is not a contrived pairing
        -- a program with a Tk view and a second renderer through another
        toolkit has both -- and letting go first costs one query.
        """
        if self.handle is None:
            return False
        from OpenGL import platform

        current: Any = platform.PLATFORM
        current.releaseCurrentContext()
        made = bool(GLX.glXMakeCurrent(self.display, self.drawable,
                                       self.handle))
        if made:
            nowCurrent(self.handle)
        return made

    def releaseCurrent(self) -> None:
        """Let go of the current context, leaving none current"""
        GLX.glXMakeCurrent(self.display, 0, None)
        nowCurrent(None)

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self.handle is not None:
            GLX.glXSwapBuffers(self.display, self.drawable)

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if it cannot"""
        from OpenGL.GLX.EXT import swap_control as _swap_control

        swap_control: Any = _swap_control
        if not swap_control.glXSwapIntervalEXT:
            return False
        try:
            swap_control.glXSwapIntervalEXT(self.display, self.drawable,
                                            int(interval))
        except Exception:
            log.debug('the driver would not set the swap interval',
                      exc_info=True)
            return False
        return True

    def destroy(self) -> None:
        """Give the context and this module's display connection back

        Called twice is called once; the second call has nothing to do.

        A ``glBegin`` block left open goes with it: a context destroyed inside
        one is undefined and a driver need not survive it, so the block is
        closed while there is still a context to close it in.  See
        :func:`OpenGL.error.end_abandoned_block`.
        """
        if self.handle is not None:
            end_abandoned_block()
            gone(self.handle)
            self.releaseCurrent()
            GLX.glXDestroyContext(self.display, self.handle)
            self.handle = None
        self._closeDisplay()

    def _closeDisplay(self) -> None:
        if self.display:
            self._x11.XCloseDisplay(self.display)
            self.display = None

    def describe(self) -> str:
        """A one-line description of what this context is, for a log line"""
        return 'GLX context on window 0x%x for %s' % (
            self.drawable or 0, self.attributes.describe())
