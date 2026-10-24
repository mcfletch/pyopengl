"""A Tk widget with an OpenGL context of its own.

:class:`GLFrame` is an ordinary ``tkinter.Frame`` that owns a GL context on its
own native window.  It packs, grids, resizes and is destroyed like any other
widget.  No Tcl extension is needed.  The context is created through the window
system's API, using the native window handle that Tk provides.

    from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor
    from OpenGL.Tk import GLFrame
    import tkinter

    class Scene(GLFrame):
        def initgl(self):                  # once, with the context current
            glClearColor(0.2, 0.3, 0.3, 1.0)
        def redraw(self):                  # per frame
            glClear(GL_COLOR_BUFFER_BIT)

    root = tkinter.Tk()
    Scene(root, width=640, height=480).pack(fill='both', expand=True)
    root.mainloop()

The context is created when the widget is mapped, because a Tk window has no
native handle before that.  To use GL immediately after creating the widget
(to load textures, or to run its own loop), a program calls
:meth:`GLFrame.waitForMap`.  It processes Tk events until the window is on
screen and the context exists.
"""

from __future__ import annotations

import logging
import time
import tkinter
from typing import Any, Optional

from OpenGL.error import end_abandoned_block
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.context import createContext
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

__all__ = ['GLFrame']

#: Seconds :meth:`GLFrame.waitForMap` waits for the window system to map the
#: window before raising.  Five seconds allows for a loaded machine without
#: hanging a program whose window is never mapped.
MAP_TIMEOUT = 5.0

#: Seconds the wait loop sleeps between checks.
MAP_POLL = 0.005


class GLFrame(tkinter.Frame):
    """A Tk frame that draws with OpenGL

    Subclass it and override :meth:`initgl` and :meth:`redraw`.  The other
    methods have working defaults.

    Context attributes can be passed as keywords alongside the ordinary Tk
    options (``profile``, ``version``, ``depthSize`` and the rest of
    :class:`~OpenGL.Tk.attributes.ContextAttributes`).  They can also be
    passed as a ready-made ``attributes`` object.  Other keywords go to
    ``tkinter.Frame``.

    Attributes:
        attributes - the requested context attributes
        context - the context object, or None before the widget is mapped;
            see :mod:`OpenGL.Tk.context` for its methods
        contextError - the exception raised while creating the context, or
            None.  It is stored rather than raised from the ``<Map>`` binding.
            Raised there, it would appear as a Tk callback error unrelated to
            the code that built the widget.  :meth:`waitForMap` and
            :meth:`makeCurrent` raise it.  Cleared when the widget is
            destroyed.
    """

    #: Milliseconds between renders while an animation is running, or 0 for
    #: none.  See :meth:`startAnimation`.
    animate = 0

    context = None
    contextError: Optional[BaseException] = None

    def __init__(
        self,
        master: Any = None,
        attributes: Optional[ContextAttributes] = None,
        cnf: Optional[dict] = None,
        **kw: Any,
    ) -> None:
        asked = {name: kw.pop(name) for name in list(kw)
                 if name in ContextAttributes.KEYWORDS}
        if attributes is not None and asked:
            raise TypeError(
                'Give either attributes or the individual context keywords '
                '(%s), not both' % (', '.join(sorted(asked)),))
        self.attributes = attributes or ContextAttributes(**asked)
        # Tk paints a widget's background over whatever GL drew, which
        # flickers on every expose.  An empty background tells Tk not to paint
        # the widget.
        kw.setdefault('background', '')
        tkinter.Frame.__init__(self, master, cnf or {}, **kw)
        self._initialised: bool = False
        self._animationJob: Optional[str] = None
        self.bind('<Map>', self._onMap)
        self.bind('<Expose>', self._onExpose)
        self.bind('<Configure>', self._onConfigure)
        self.bind('<Destroy>', self._onDestroy)

    ### customisation points
    def initgl(self) -> None:
        """Create the GL resources this widget draws with

        Called once, with the context current, as soon as the context exists.
        Create textures, shaders and buffers here.  No context exists before
        this call, and it is not repeated when the widget is resized or
        re-exposed.
        """

    def redraw(self) -> None:
        """Draw one frame

        Called with the context current; :meth:`render` swaps the buffers
        afterwards.
        """

    def reshape(self, width: int, height: int) -> None:
        """Update GL state for the widget's new size

        The default sets the viewport to the whole widget.  Called with the
        context current.
        """
        from OpenGL.GL import glViewport

        glViewport(0, 0, width, height)

    ### the context's life
    def createContext(self) -> Any:
        """This widget's GL context, created if it does not exist yet

        Raises :class:`~OpenGL.Tk.errors.TkContextError` if no context can be
        created.  The widget still works as an ordinary frame, so a program can
        catch the error and fall back to something else.
        """
        if self.context is not None:
            return self.context
        # A context cannot be created while a glBegin block is open on the
        # current one.  That happens when a widget is mapped from inside a
        # redraw.  See OpenGL.error.end_abandoned_block.
        end_abandoned_block()
        self.update_idletasks()         # so winfo_id() names a real window
        self.context = createContext(self, self.attributes)
        self.contextError = None
        interval = self.attributes.swapInterval
        if interval is not None and self.context.makeCurrent():
            self.context.setSwapInterval(interval)
        log.debug('created %s', self.context.describe())
        return self.context

    def destroyContext(self) -> None:
        """Destroy this widget's context

        Called automatically when the widget is destroyed.  A second call does
        nothing.  The context's textures, buffers and programs are destroyed
        with it.  A program that caches GL names per context should use
        PyOpenGL's context tracking to learn of this.
        """
        self.stopAnimation()
        context, self.context = self.context, None
        if context is not None:
            context.destroy()
        self._initialised = False

    def waitForMap(self, timeout: float = MAP_TIMEOUT) -> Any:
        """The context, after processing Tk events until the window is mapped

        A Tk window has no native handle until the window system maps it, so
        no context can be created before then.  Scripts, tests and programs
        with their own loop call this to use GL immediately after creating the
        widget.

        Raises :class:`~OpenGL.Tk.errors.TkContextError` if the window is not
        mapped within ``timeout`` seconds.  Re-raises the stored
        :attr:`contextError` if creating the context failed.
        """
        deadline = time.time() + timeout
        while self.context is None and time.time() < deadline:
            self.update()
            if self.contextError is not None:
                raise self.contextError
            if self.context is None:
                time.sleep(MAP_POLL)
        if self.context is None:
            raise TkContextError(
                'The window system did not map this widget within %.1f '
                'seconds, so there is no window to make a context on'
                % (timeout,))
        return self.context

    ### drawing
    def makeCurrent(self) -> bool:
        """Make this widget's context current; False if it has none yet

        Returns False before the widget is mapped.  Raises the stored
        :attr:`contextError` if creating the context failed.
        """
        if self.contextError is not None:
            raise self.contextError
        if self.context is None:
            return False
        return self.context.makeCurrent()

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self.context is not None:
            self.context.swapBuffers()

    def render(self) -> bool:
        """Draw one frame and show it; False if there is nothing to draw into

        Makes the context current, calls :meth:`redraw`, then swaps buffers.  A
        program with its own loop calls this.  The widget also calls it on
        expose and while an animation is running.
        """
        if not self.makeCurrent():
            return False
        self.redraw()
        self.swapBuffers()
        return True

    def setSwapInterval(self, interval: int) -> bool:
        """Set the swap interval; False if it cannot be set

        One caps the frame rate at the display's refresh rate.  Zero draws as
        fast as the driver allows, for benchmarks.
        """
        if self.context is None:
            return False
        return bool(self.context.setSwapInterval(interval))

    ### an animation, for a widget that is not driven from outside
    def startAnimation(self, interval: Optional[int] = None) -> None:
        """Render every ``interval`` milliseconds until :meth:`stopAnimation`

        Use this for a widget whose scene changes over time.  A program with
        its own loop calls :meth:`render` from that loop instead.
        """
        if interval is not None:
            self.animate = int(interval)
        self.stopAnimation()
        if self.animate > 0:
            self._animationJob = self.after(self.animate, self._animationStep)

    def stopAnimation(self) -> None:
        """Stop the animation started by :meth:`startAnimation`"""
        job, self._animationJob = self._animationJob, None
        if job is not None:
            try:
                self.after_cancel(job)
            except tkinter.TclError:
                pass                    # the interpreter is shutting down

    def _animationStep(self) -> None:
        self._animationJob = None
        self.render()
        if self.animate > 0 and self.winfo_exists():
            self._animationJob = self.after(self.animate, self._animationStep)

    ### Tk bindings
    def _onMap(self, event: Any = None) -> None:
        """Create the context once the window system has mapped the widget"""
        if self.context is not None:
            return
        try:
            self.createContext()
        except Exception as error:  # noqa: BLE001 kept as contextError and raised by waitForMap and makeCurrent
            # Stored rather than raised.  An exception from a Tk binding appears
            # as a callback error unrelated to the code that built the widget.
            # waitForMap and makeCurrent raise it to their caller.
            self.contextError = error
            # Log strings rather than the objects.  A handler that keeps
            # records (a MemoryHandler, a QueueHandler, a test's log capture)
            # would keep this widget and its Tk root alive with the record.
            # The root would then be freed on whichever thread drops the
            # record last.
            log.error('could not make a GL context for %s: %s',  # noqa: TRY400 a record holding the traceback would hold its frames, and through them this widget
                      str(self), str(error))
            return
        self._ensureInitialised()
        self.render()

    def _ensureInitialised(self) -> None:
        """Run ``initgl`` once, with the context current"""
        if self._initialised or self.context is None:
            return
        self._initialised = True
        if self.makeCurrent():
            self.initgl()

    def _onExpose(self, event: Any = None) -> None:
        """Redraw after part of the widget has been uncovered"""
        if self.context is None:
            return
        self._ensureInitialised()
        self.render()

    def _onConfigure(self, event: Any = None) -> None:
        """Call :meth:`reshape` with the widget's new size and redraw

        ``initgl`` is not run again.  A resize keeps the same context, and
        re-running it would rebuild every texture and shader on each resize.
        """
        if self.context is None:
            return
        width = int(getattr(event, 'width', 0) or self.winfo_width())
        height = int(getattr(event, 'height', 0) or self.winfo_height())
        if width <= 0 or height <= 0:
            return
        if self.makeCurrent():
            self.reshape(width, height)
        self.render()

    def _onDestroy(self, event: Any = None) -> None:
        """Destroy the context and clear :attr:`contextError` with the widget"""
        if event is not None and event.widget is not self:
            return                      # a child widget was destroyed
        self.destroyContext()
        # A stored error holds the frames it was raised through, and they hold
        # this widget.  Kept after destruction, that forms a cycle only the
        # garbage collector breaks.  The root's Tcl interpreter is then
        # deleted on whichever thread the collector runs on, and Tcl aborts
        # the process.
        self.contextError = None

    ### method names of the Togl-based widget
    def tkRedraw(self, *arguments: Any) -> None:
        """Draw one frame; :meth:`render` under the Togl widget's name"""
        self.render()

    def tkMakeCurrent(self) -> bool:
        """:meth:`makeCurrent`, under the Togl widget's name"""
        return self.makeCurrent()

    def tkSwapBuffers(self) -> None:
        """:meth:`swapBuffers`, under the Togl widget's name"""
        self.swapBuffers()
