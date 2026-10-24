"""An OpenGL context on a Tk widget's X11 window.

Tk provides the X window id (``winfo_id()``), and GLX creates a context for
that window in two steps.  :func:`configAttributes` and
:func:`contextAttributes` translate a
:class:`~OpenGL.Tk.attributes.ContextAttributes` into the attribute list for
each step:

* choose a framebuffer configuration (``glXChooseFBConfig``), and
* create a context on it (``glXCreateContextAttribsARB``, which takes the
  profile and version).

X assigns a visual to a window when the window is created.  A context can only
be made current on a window whose visual matches the context's configuration.
The configuration is therefore chosen from those that match the visual Tk gave
the widget.  An X window cannot change its visual after creation, so this
module does not try to recreate the widget.
"""

from __future__ import annotations

import ctypes
import logging
from typing import Any, Optional

from OpenGL import GL, GLX
from OpenGL.GLX.ARB import create_context as _create_context
from OpenGL.GLX.ARB import create_context_profile as _create_context_profile
from OpenGL.error import end_abandoned_block
from OpenGL.platform import ctypesloader
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.context import gone, nowCurrent
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

# The constants and entry points in these two modules come from PyOpenGL's
# generated declaration tables at import time, so a type checker reading the
# source cannot find them by name.  They are aliased through Any, which avoids
# about forty separate suppressions in this module.
create_context: Any = _create_context
create_context_profile: Any = _create_context_profile

__all__ = ['GLXContext', 'configAttributes', 'contextAttributes']


def configAttributes(attributes: ContextAttributes) -> list[int]:
    """The ``glXChooseFBConfig`` attribute list for ``attributes``

    Terminated with ``GL_NONE``, as that call requires.  Multisampling and
    stereo are only included when requested.  ``glXChooseFBConfig`` treats a
    listed attribute as a minimum, and a driver with no matching
    configuration returns none.
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


def contextAttributes(attributes: ContextAttributes) -> list[int]:
    """The ``glXCreateContextAttribsARB`` attribute list for ``attributes``

    Terminated with 0.  A ``legacy`` request has no version and no profile.
    It is created through ``glXCreateNewContext`` instead; see
    :meth:`GLXContext._create`.
    """
    wanted: list[int] = []
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
    """The X error report passed to an error handler

    Declared only up to ``resourceid``.  The real structure is longer, but no
    later field is read here.
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


#: The callback type ``XSetErrorHandler`` takes.  Defined at module scope
#: because a ctypes callback must outlive every call that can reach it.
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
    """Collect X errors raised inside the block instead of exiting

    Xlib's default error handler prints to stderr and calls ``exit()``.  A
    request for a GL version the driver does not support would then end the
    application instead of raising an exception it can catch.

    X reports errors asynchronously, so requests must be flushed and replies
    read before the block ends.  :meth:`sync` does that, and ``__exit__``
    calls it.

    ``XSetErrorHandler`` is process-wide and Xlib has no per-display handler,
    so this class is not thread-safe.
    """

    def __init__(self, library: Any, display: Any) -> None:
        self.library = library
        self.display = display
        self.errors: list[str] = []
        self._previous = None
        self._handler = ERROR_HANDLER(self._collect)

    def _collect(self, display: Any, event: Any) -> int:
        report = event.contents
        self.errors.append(
            'X error %d on request %d.%d'
            % (report.error_code, report.request_code, report.minor_code))
        return 0

    def sync(self) -> None:
        """Flush pending requests and process the server's replies"""
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

    Created by :func:`OpenGL.Tk.context.createContext` and available as
    ``frame.context``.

    Attributes:
        handle - the driver's ``GLXContext``; PyOpenGL's per-context dispatch
            tables are keyed by it
        display - the ``Display*`` of this context's X connection
        drawable - the X window id it draws into
    """

    handle = None
    display = None
    drawable = None

    def __init__(self, widget: Any, attributes: ContextAttributes) -> None:
        self.attributes = attributes
        self._x11 = _x11()
        # This module opens its own X connection because Tk does not expose
        # its Display*.  A second connection to the same server can draw into
        # the same window, since the window id identifies the target.
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

        A context can only be current on a window whose visual matches its
        configuration.  Tk chose the widget's visual when it created the
        window, so the search is limited to configurations on that visual.  On
        some servers Tk's default visual has no depth buffer, and nothing
        matches.  The first matching configuration is then used and the
        mismatch is logged, because a context on the wrong visual fails with
        an unexplained ``BadMatch``.
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

        Indexing a ctypes pointer array returns a view onto the array's
        memory.  After ``XFree`` releases the array, the handle reads whatever
        is in the freed block.  The driver then reports ``GLXBadFBConfig``,
        and Xlib's default error handler exits the process.  ``cast`` builds an
        object that holds the address itself.
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
        """The new context handle; raises TkContextError with the reason

        A version or profile can only be requested through
        ``ARB_create_context``.  A driver without that extension only supports
        ``glXCreateNewContext``, which is also what a ``legacy`` request uses.
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
            # X reports a refusal asynchronously, so flush the request and read
            # the reply before checking the result.
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
        """Make this context current; False if the driver refused

        Any context current on the thread is released first.  A thread has at
        most one current context, and EGL and GLX do not track each other.
        Calling ``glXMakeCurrent`` while an EGL context is current is an X
        ``BadAccess``, and Xlib's default error handler exits the process.  A
        program with a Tk view and a second renderer in another toolkit can
        have both.  The release costs one query.
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
        """Release the current context, leaving none current"""
        GLX.glXMakeCurrent(self.display, 0, None)
        nowCurrent(None)

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self.handle is not None:
            GLX.glXSwapBuffers(self.display, self.drawable)

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if unsupported"""
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
        """Destroy the context and close this module's display connection

        A second call does nothing.

        An open ``glBegin`` block is closed first.  Destroying a context inside
        one is undefined behaviour, and some drivers crash.  See
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
        """A one-line description of this context, for a log line"""
        return 'GLX context on window 0x%x for %s' % (
            self.drawable or 0, self.attributes.describe())
