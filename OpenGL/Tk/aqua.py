"""An OpenGL context on a Tk widget's place in a macOS window.

Tk on Aqua has no window id to make a context against.  Its widgets are
rectangles drawn into the one ``NSView`` that fills each toplevel, so
``winfo_id()`` names nothing a GL context could be attached to.  What a context
can be attached to is a view, so this module makes one: a plain ``NSView``
added to the toplevel's content view, kept over the widget's rectangle, with an
``NSOpenGLContext`` drawing into it.

The pixel format and the profile come from :mod:`OpenGL.CGL`, which is what
the headless test backend uses too: :func:`cglProfile` turns a
:class:`~OpenGL.Tk.attributes.ContextAttributes` into one of its profiles, and
:func:`OpenGL.CGL.pixel_format_candidates` into the attribute lists to try, a
GPU renderer first and the CPU one where a machine has no other.

* The view sits **above** Tk's own drawing.  A Tk widget placed over a GL
  widget is covered by it, and a widget that is unmapped hides the view.
* The surface has the widget's size in points, not pixels.  On a Retina
  display it is scaled up by the system, which keeps ``glViewport(0, 0,
  winfo_width(), winfo_height())`` correct.
* macOS provides OpenGL up to 4.1, and a compatibility profile only at 2.1
  (``profile='legacy'``, or ``'compatibility'`` with ``version=None``).  A
  request for anything else raises :class:`~OpenGL.Tk.errors.TkContextError`
  saying so.  A pixel format has no debug attribute, so ``debug=True`` makes an
  ordinary context.

Everything that decides something is a plain function taking plain values --
:func:`cglProfile`, :func:`viewFrame`, :func:`widgetOffset`,
:func:`chooseWindow` -- so it is readable and testable without a Mac.
:class:`AquaContext` sends the messages.
"""

from __future__ import annotations

import ctypes
import logging
import tkinter
import uuid
from typing import Any, Optional, Sequence

from OpenGL import CGL
from OpenGL.error import end_abandoned_block
from OpenGL.Tk import cocoa
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.context import gone, nowCurrent
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

__all__ = [
    'AquaContext', 'chooseWindow', 'cglProfile', 'swapIntervalFor', 'viewFrame',
    'widgetOffset',
]

#: ``NSOpenGLPixelFormatAttribute`` is an unsigned 32-bit integer.
NSOpenGLPixelFormatAttribute = ctypes.c_uint32


def cglProfile(attributes: ContextAttributes) -> str:
    """The :data:`OpenGL.CGL.PROFILES` name serving a request

    Raises :class:`~OpenGL.Tk.errors.TkContextError` saying why where macOS
    has nothing to give: a version above 4.1, a compatibility profile above
    2.1, or a core profile below 3.2.

    A request that names no profile-bearing version (``legacy``, or any
    profile with a version below 3.2) is a plain 2.1 context, which is what
    every windowing toolkit gives for it.
    """
    version = tuple(attributes.version or (0, 0))
    if version > CGL.MAX_VERSION:
        raise TkContextError(
            'macOS provides OpenGL up to %d.%d; %d.%d was asked for'
            % (CGL.MAX_VERSION + version))
    profile = 'core' if (attributes.profile == 'core'
                         and attributes.profileApplies()) else 'compatibility'
    name, refusal = CGL.profile_for('gl', profile, version)
    if name is None:
        hint = ''
        if profile == 'compatibility':
            hint = (
                '; ask for profile="legacy" (or version=None) for the 2.1 '
                'fixed-function context, or profile="core" for shaders')
        raise TkContextError('%s%s' % (refusal, hint))
    return name


def swapIntervalFor(attributes: ContextAttributes) -> int:
    """The swap interval a new context is given: the request's, or zero

    A windowed context is composited and synchronised to the display by the
    window server.  An interval of one on top of that waits for a refresh that
    a machine without a display never delivers, and the swap does not return.
    """
    interval = attributes.swapInterval
    return 0 if interval is None else interval


def pixelFormatSizes(attributes: ContextAttributes) -> dict[str, Any]:
    """The sizes and switches :func:`OpenGL.CGL.pixel_format_attributes` takes

    CGL counts the three colour channels as one size.
    """
    return dict(
        color_size=(attributes.redSize + attributes.greenSize
                    + attributes.blueSize),
        alpha_size=attributes.alphaSize,
        depth_size=attributes.depthSize,
        stencil_size=attributes.stencilSize,
        samples=attributes.samples,
        double_buffer=attributes.doubleBuffer,
        stereo=attributes.stereo,
    )


def widgetOffset(widget: Any, toplevel: Any) -> tuple[int, int]:
    """Where ``widget``'s top-left corner is in ``toplevel``, in Tk points

    Summed up the parent chain from ``winfo_x`` and ``winfo_y``, which Tk
    answers relative to the parent, so it is the same whatever window decoration
    the toplevel has.
    """
    x = y = 0
    current = widget
    while current is not None and current is not toplevel:
        x += int(current.winfo_x())
        y += int(current.winfo_y())
        current = current.master
    return x, y


def viewFrame(
    offset: tuple[int, int],
    size: tuple[int, int],
    hostHeight: int,
    flipped: bool,
) -> tuple[float, float, float, float]:
    """The ``(x, y, width, height)`` to give the view in its superview

    ``offset`` is the widget's top-left in the toplevel with y growing
    downwards, as Tk counts.  A flipped superview counts the same way; an
    ordinary one has its origin at the bottom-left, so the view's lower edge is
    measured up from the bottom of a host ``hostHeight`` high.
    """
    x, y = offset
    width, height = size
    if not flipped:
        y = hostHeight - y - height
    return (float(x), float(y), float(width), float(height))


def chooseWindow(
    candidates: Sequence[Any],
    matches: Any,
) -> Optional[Any]:
    """The one of ``candidates`` that is the toplevel being looked for

    ``matches(candidate)`` answers whether it is.  A single candidate is taken
    without asking, since there is nothing to tell apart; with several, exactly
    one has to match, and ``None`` is the answer to none or to more than one.
    """
    if len(candidates) == 1:
        return candidates[0]
    found = [candidate for candidate in candidates if matches(candidate)]
    return found[0] if len(found) == 1 else None


def unbind(widget: Any, sequence: str, identifier: str) -> None:
    """Remove the one binding ``identifier`` that ``widget.bind`` made

    ``Misc.unbind(sequence, funcid)`` removes every binding of the sequence on
    the Pythons before 3.12, which would take the widget's own with it.  The
    script is read back and the line naming this command left out instead.
    """
    try:
        script = str(widget.tk.call('bind', widget._w, sequence))
        kept = '\n'.join(
            line for line in script.split('\n') if identifier not in line)
        widget.tk.call('bind', widget._w, sequence, kept)
        widget.deletecommand(identifier)
    except tkinter.TclError:
        pass                    # the widget is already gone with its bindings


class AquaContext(object):
    """A GL context drawing into an ``NSView`` over a Tk widget

    Built by :func:`OpenGL.Tk.context.createContext`; a caller reaches it as
    ``frame.context``.

    Attributes:
        handle -- the ``CGLContextObj`` the driver made, which is what
            PyOpenGL's per-context dispatch tables are keyed by
        profile -- the :data:`OpenGL.CGL.PROFILES` name it was made with
        renderer -- ``'accelerated'``, ``'any'`` or ``'software'``
    """

    handle: Optional[int] = None
    profile: Optional[str] = None
    renderer: Optional[str] = None
    _host: Optional[int] = None
    _frame: Optional[tuple[float, float, float, float]] = None

    def __init__(self, widget: Any, attributes: ContextAttributes) -> None:
        try:
            self.objc = cocoa.runtime()
        except cocoa.CocoaError as error:
            raise TkContextError(str(error)) from error
        self.attributes = attributes
        self.widget: Any = widget
        self.toplevel = widget.winfo_toplevel()
        self._context: Optional[int] = None
        self._view: Optional[int] = None
        self._bindings: list[tuple[Any, str, str]] = []
        self._shown = True
        profile = cglProfile(attributes)
        if attributes.debug:
            log.debug('a pixel format has no debug attribute; making an '
                      'ordinary context')
        try:
            with self.objc.pool():
                self._createContext(profile)
                self._createView()
                self._attach()
            self.profile = profile
            self._checkVersion()
        except Exception:
            self.destroy()
            raise
        self._follow()

    ### creation
    def _createContext(self, profile: str) -> None:
        objc = self.objc
        share = self._shareContext()
        format_ = self._pixelFormat(profile)
        log.debug('pixel format %#x (%s renderer); making the context',
                  format_, self.renderer)
        try:
            made = objc.send(
                objc.send(objc.cls('NSOpenGLContext'), 'alloc'),
                'initWithFormat:shareContext:', format_, share,
                argtypes=(cocoa.ID, cocoa.ID))
        finally:
            objc.release(format_)
        if not made:
            raise TkContextError(
                'The driver would not create a context for %s'
                % (self.attributes.describe(),))
        self._context = made
        log.debug('NSOpenGLContext %#x', made)
        cgl = objc.send(made, 'CGLContextObj')
        if not cgl:
            raise TkContextError('NSOpenGLContext has no CGL context')
        self.handle = int(cgl)

    def _shareContext(self) -> Optional[int]:
        share = self.attributes.share
        if share is None:
            return None
        found = getattr(share, '_context', None)
        if found is None:
            raise TkContextError(
                'Only another OpenGL.Tk context on Aqua can be shared with '
                'here; %r is not one' % (share,))
        return int(found)

    def _pixelFormat(self, profile: str) -> int:
        """An ``NSOpenGLPixelFormat`` the machine can serve, owned by the caller

        Each renderer kind of :func:`OpenGL.CGL.pixel_format_candidates` is
        tried in turn, and the first the machine offers is taken.
        """
        objc = self.objc
        sizes = pixelFormatSizes(self.attributes)
        for kind, array in CGL.pixel_format_candidates(profile, **sizes):
            made = objc.send(
                objc.send(objc.cls('NSOpenGLPixelFormat'), 'alloc'),
                'initWithAttributes:', ctypes.cast(array, ctypes.c_void_p),
                argtypes=(ctypes.c_void_p,))
            if made:
                self.renderer = kind
                return made
            log.debug('no %s renderer for the %s profile', kind, profile)
        raise TkContextError(
            'No pixel format for %s: the %s profile is not offered by any '
            'renderer on this machine' % (self.attributes.describe(), profile))

    def _createView(self) -> None:
        """The ``NSView`` added to the toplevel's content view, still empty"""
        objc = self.objc
        host = self._hostView()
        log.debug('host view %#x (%s)', host, objc.className(host))
        view = objc.new('NSView')
        self._view = view
        self._host = host
        # The frame is set once there is a window to measure against; see
        # resize().  Tk's content view goes on drawing the widgets, and this
        # view sits above them.
        objc.send(host, 'addSubview:', view, argtypes=(cocoa.ID,),
                  restype=None)

    def _attach(self) -> None:
        """Point the context at the view and make it the size of the widget"""
        objc = self.objc
        # Placed before it is attached: a context is told about a view that
        # moves or resizes with ``update``, and a view that is attached where
        # it is going to stay has nothing to be told.
        self.resize(update=False)
        log.debug('setView:')
        objc.send(self._context, 'setView:', self._view,
                  argtypes=(cocoa.ID,), restype=None)

    def _checkVersion(self) -> None:
        """Refuse a context that is lower than the profile it was made with

        CGL accepts a pixel format naming the 3.2 core profile on a renderer
        that implements 2.1, and answers with a 2.1 context.  macOS resolves
        every entry point from the framework whether or not the context has it,
        so the first 3.x call on that context is a crash rather than an error.
        """
        from OpenGL.GL import GL_VERSION, glGetString

        log.debug('makeCurrent')
        if not self.makeCurrent():
            raise TkContextError('The new context would not become current')
        log.debug('glGetString')
        reported = glGetString(GL_VERSION)
        if isinstance(reported, bytes):
            reported = reported.decode('ascii', 'replace')
        interval = swapIntervalFor(self.attributes)
        log.debug('swap interval %d', interval)
        if not self.setSwapInterval(interval):
            log.debug('the renderer would not take a swap interval')
        shortfall = CGL.version_shortfall(
            reported, CGL.PROFILE_VERSIONS[self.profile or 'legacy'])
        if shortfall:
            raise TkContextError(
                'The %s renderer cannot serve %s: %s'
                % (self.renderer, self.attributes.describe(), shortfall))

    ### finding the window
    def _hostView(self) -> int:
        """The content view of the ``NSWindow`` that is this widget's toplevel"""
        objc = self.objc
        application = objc.send(objc.cls('NSApplication'),
                                'sharedApplication')
        windows = [
            window for window in objc.items(objc.send(application, 'windows'))
            if objc.send(window, 'contentView')
        ]
        # Tk's own content view class first: a process with other windows in it
        # (a second toolkit, a file dialog) has views that are not Tk's.
        tkWindows = [
            window for window in windows
            if objc.className(objc.send(window, 'contentView'))
            .startswith('TK')
        ] or windows
        window = chooseWindow(tkWindows, self._isOurToplevel)
        if window is None:
            raise TkContextError(
                'Could not tell which of the %d windows in this process is '
                'the toplevel %s' % (len(tkWindows), self.toplevel))
        return objc.send(window, 'contentView')

    def _isOurToplevel(self, window: int) -> bool:
        """Whether ``window`` is the toplevel's, found by what it is titled

        Tk keeps no handle to an ``NSWindow`` that a script can read, and
        nothing else a Tk toplevel and its window share is unique -- two
        toplevels can have one size and one position.  So the toplevel is given
        a title nothing else has for the length of the question, and the
        window wearing it is the one.
        """
        previous = self.toplevel.wm_title()
        token = 'OpenGL.Tk %s' % (uuid.uuid4().hex,)
        self.toplevel.wm_title(token)
        try:
            self.toplevel.update_idletasks()
            return self.objc.text(self.objc.send(window, 'title')) == token
        finally:
            self.toplevel.wm_title(previous)
            self.toplevel.update_idletasks()

    ### keeping the view where the widget is
    def _follow(self) -> None:
        """Move and hide the view as the widget and its toplevel do"""
        self._bind(self.widget, '<Configure>', self._onGeometry)
        self._bind(self.widget, '<Unmap>', self._onUnmap)
        self._bind(self.widget, '<Map>', self._onMap)
        if self.toplevel is not self.widget:
            self._bind(self.toplevel, '<Configure>', self._onGeometry)

    def _bind(self, widget: Any, sequence: str, handler: Any) -> None:
        identifier = widget.bind(sequence, handler, add='+')
        self._bindings.append((widget, sequence, identifier))

    def _onGeometry(self, event: Any = None) -> None:
        self.resize()

    def _onUnmap(self, event: Any = None) -> None:
        self._show(False)

    def _onMap(self, event: Any = None) -> None:
        self._show(True)
        self.resize()

    def _show(self, shown: bool) -> None:
        if self._view is None or shown == self._shown:
            return
        self._shown = shown
        with self.objc.pool():
            self.objc.send(self._view, 'setHidden:', int(not shown),
                           argtypes=(cocoa.BOOL,), restype=None)

    def resize(self, update: bool = True) -> None:
        """Put the view over the widget again and tell the context its size

        Called for you as the widget and its toplevel change.  The context is
        told only when the view's frame is different from the last one it was
        given, and only if ``update`` is true.  A no-op once the context is
        gone.
        """
        if self._view is None or self._context is None:
            return
        objc = self.objc
        width = max(int(self.widget.winfo_width()), 1)
        height = max(int(self.widget.winfo_height()), 1)
        with objc.pool():
            flipped = bool(objc.send(self._host, 'isFlipped',
                                     restype=cocoa.BOOL))
            x, y, w, h = viewFrame(
                widgetOffset(self.widget, self.toplevel), (width, height),
                int(self.toplevel.winfo_height()), flipped)
            frame = (x, y, w, h)
            if frame == self._frame:
                return
            self._frame = frame
            objc.send(self._view, 'setFrame:', cocoa.CGRect(x, y, w, h),
                      argtypes=(cocoa.CGRect,), restype=None)
            if update:
                log.debug('update')
                objc.send(self._context, 'update', restype=None)

    ### the context protocol
    def makeCurrent(self) -> bool:
        """Draw into this widget from now on; False if the driver refused"""
        if self._context is None:
            return False
        with self.objc.pool():
            self.objc.send(self._context, 'makeCurrentContext', restype=None)
        made = CGL.library().CGLGetCurrentContext() == self.handle
        if made:
            nowCurrent(self.handle)
        return made

    def releaseCurrent(self) -> None:
        """Let go of the current context, leaving none current"""
        CGL.library().CGLSetCurrentContext(None)
        nowCurrent(None)

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self._context is not None:
            log.debug('flushBuffer')
            with self.objc.pool():
                self.objc.send(self._context, 'flushBuffer', restype=None)
            log.debug('flushed')

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if it cannot"""
        if self.handle is None:
            return False
        return CGL.set_swap_interval(ctypes.c_void_p(self.handle), interval)

    def destroy(self) -> None:
        """Give the context and its view back

        Called twice is called once; the second call has nothing to do.

        A ``glBegin`` block left open goes with it: a context destroyed inside
        one is undefined and a driver need not survive it, so the block is
        closed while there is still a context to close it in.  See
        :func:`OpenGL.error.end_abandoned_block`.
        """
        for widget, sequence, identifier in self._bindings:
            unbind(widget, sequence, identifier)
        self._bindings = []
        objc = self.objc
        if self.handle is not None:
            end_abandoned_block()
            gone(self.handle)
            if CGL.library().CGLGetCurrentContext() == self.handle:
                self.releaseCurrent()
            self.handle = None
        with objc.pool():
            if self._context is not None:
                objc.send(self._context, 'clearDrawable', restype=None)
                objc.release(self._context)
                self._context = None
            if self._view is not None:
                objc.send(self._view, 'removeFromSuperview', restype=None)
                objc.release(self._view)
                self._view = None
        self._host = None
        self.widget = None

    def describe(self) -> str:
        """A one-line description of what this context is, for a log line"""
        return 'NSOpenGLContext (%s profile, %s renderer) for %s' % (
            self.profile, self.renderer, self.attributes.describe())
