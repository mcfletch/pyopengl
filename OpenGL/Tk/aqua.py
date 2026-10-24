"""An OpenGL context over a Tk widget in a macOS window.

Tk on Aqua has no per-widget native window.  Its widgets are rectangles drawn
into the single ``NSView`` that fills each toplevel, so ``winfo_id()`` gives
nothing a GL context can attach to.  A GL context on macOS attaches to an
``NSView``.  This module adds a plain ``NSView`` to the toplevel's content
view, keeps it over the widget's rectangle, and attaches an
``NSOpenGLContext`` to it.

The pixel format and profile come from :mod:`OpenGL.CGL`, which the headless
test backend also uses.  :func:`cglProfile` converts a
:class:`~OpenGL.Tk.attributes.ContextAttributes` into a CGL profile name.
:func:`OpenGL.CGL.pixel_format_candidates` converts it into attribute lists to
try, a GPU renderer first and then the CPU renderer.

* The view is drawn above Tk's own drawing.  A Tk widget placed over a GL
  widget is hidden by the view.  Unmapping the GL widget hides the view.
* The surface has the widget's size in points.  On a Retina display the system
  scales it up, so ``glViewport(0, 0, winfo_width(), winfo_height())`` stays
  correct.
* macOS provides OpenGL up to 4.1, and a compatibility profile only at 2.1
  (``profile='legacy'``, or ``'compatibility'`` with ``version=None``).  Any
  other request raises :class:`~OpenGL.Tk.errors.TkContextError` with the
  reason.  A pixel format has no debug attribute, so ``debug=True`` creates an
  ordinary context.

The decisions are made by plain functions that take plain values
(:func:`cglProfile`, :func:`viewFrame`, :func:`widgetOffset`,
:func:`chooseWindow`), so they can be tested without a Mac.
:class:`AquaContext` sends the Objective-C messages.
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
    """The :data:`OpenGL.CGL.PROFILES` name for ``attributes``

    Raises :class:`~OpenGL.Tk.errors.TkContextError` with the reason when
    macOS has no matching context: a version above 4.1, a compatibility
    profile above 2.1, or a core profile below 3.2.

    A request without a profile-bearing version (``legacy``, or any profile
    with a version below 3.2) gets a plain 2.1 context, as in other windowing
    toolkits.
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
    """The requested swap interval for a new context, or zero

    The window server composites a windowed context and synchronises it to the
    display.  An interval of one adds a wait for a refresh.  On a machine
    without a display that refresh never arrives, and the swap does not return.
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
    """The ``(x, y)`` of ``widget``'s top-left corner in ``toplevel``, in points

    Summed up the parent chain from ``winfo_x`` and ``winfo_y``, which Tk
    reports relative to the parent.  The result does not depend on the
    toplevel's window decoration.
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

    ``offset`` is the widget's top-left in the toplevel, with y increasing
    downwards as in Tk.  A flipped superview uses the same convention.  An
    ordinary superview has its origin at the bottom-left, so the view's lower
    edge is measured up from the bottom of a host ``hostHeight`` high.
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
    """The candidate window that is the toplevel, or None

    ``matches(candidate)`` returns whether a candidate is the toplevel.  A
    single candidate is returned without calling ``matches``.  With several,
    exactly one must match.  Returns ``None`` if none or more than one match.
    """
    if len(candidates) == 1:
        return candidates[0]
    found = [candidate for candidate in candidates if matches(candidate)]
    return found[0] if len(found) == 1 else None


def unbind(widget: Any, sequence: str, identifier: str) -> None:
    """Remove the single binding ``identifier`` made by ``widget.bind``

    Before Python 3.12, ``Misc.unbind(sequence, funcid)`` removes every
    binding of the sequence, including the widget's own.  This function reads
    the binding script back and rewrites it without the line naming this
    command.
    """
    try:
        script = str(widget.tk.call('bind', widget._w, sequence))
        kept = '\n'.join(
            line for line in script.split('\n') if identifier not in line)
        widget.tk.call('bind', widget._w, sequence, kept)
        widget.deletecommand(identifier)
    except tkinter.TclError:
        pass                    # the widget and its bindings are destroyed


class AquaContext(object):
    """A GL context drawing into an ``NSView`` over a Tk widget

    Created by :func:`OpenGL.Tk.context.createContext` and available as
    ``frame.context``.

    Attributes:
        handle - the driver's ``CGLContextObj``; PyOpenGL's per-context
            dispatch tables are keyed by it
        profile - the :data:`OpenGL.CGL.PROFILES` name it was created with
        renderer - ``'accelerated'``, ``'any'`` or ``'software'``
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
        """An ``NSOpenGLPixelFormat`` this machine supports, owned by the caller

        Each renderer kind from :func:`OpenGL.CGL.pixel_format_candidates` is
        tried in turn, and the first one the machine supports is used.
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
        """Add an empty ``NSView`` to the toplevel's content view"""
        objc = self.objc
        host = self._hostView()
        log.debug('host view %#x (%s)', host, objc.className(host))
        view = objc.new('NSView')
        self._view = view
        self._host = host
        # The frame is set later by resize(), once there is a window to
        # measure.  Tk's content view still draws the widgets, and this view
        # is drawn above them.
        objc.send(host, 'addSubview:', view, argtypes=(cocoa.ID,),
                  restype=None)

    def _attach(self) -> None:
        """Size the view to the widget and attach the context to it"""
        objc = self.objc
        # The view is placed before attaching.  A context needs an ``update``
        # message only when its view moves or resizes after attaching.
        self.resize(update=False)
        log.debug('setView:')
        objc.send(self._context, 'setView:', self._view,
                  argtypes=(cocoa.ID,), restype=None)

    def _checkVersion(self) -> None:
        """Raise TkContextError if the context's version is below its profile's

        CGL accepts a pixel format naming the 3.2 core profile on a renderer
        that implements 2.1, and returns a 2.1 context.  macOS resolves every
        entry point from the framework whether or not the context supports
        it, so the first 3.x call on that context crashes the process.
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
        # Prefer windows whose content view is Tk's class.  A process can also
        # have windows from a second toolkit or a file dialog.
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
        """Whether ``window`` is the toplevel's ``NSWindow``, matched by title

        Tk exposes no ``NSWindow`` handle to scripts.  Size and position do not
        identify a window, because two toplevels can share both.  The toplevel
        is given a unique temporary title, and the window with that title is
        the match.  The original title is then restored.
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
        """Bind events that move, show and hide the view with the widget"""
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
        """Move the view over the widget and send the context ``update``

        Called automatically when the widget or its toplevel changes.  The
        view's frame is set only when it differs from the last frame.  The
        context receives ``update`` only then, and only if ``update`` is true.
        Does nothing after the context is destroyed.
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
        """Make this context current; False if the driver refused"""
        if self._context is None:
            return False
        with self.objc.pool():
            self.objc.send(self._context, 'makeCurrentContext', restype=None)
        made = CGL.library().CGLGetCurrentContext() == self.handle
        if made:
            nowCurrent(self.handle)
        return made

    def releaseCurrent(self) -> None:
        """Release the current context, leaving none current"""
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
        """Wait ``interval`` refreshes between swaps; False if unsupported"""
        if self.handle is None:
            return False
        return CGL.set_swap_interval(ctypes.c_void_p(self.handle), interval)

    def destroy(self) -> None:
        """Release the context and remove its view

        A second call does nothing.

        An open ``glBegin`` block is closed first.  Destroying a context inside
        one is undefined behaviour, and some drivers crash.  See
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
        self.toplevel = None

    def describe(self) -> str:
        """A one-line description of this context, for a log line"""
        return 'NSOpenGLContext (%s profile, %s renderer) for %s' % (
            self.profile, self.renderer, self.attributes.describe())
