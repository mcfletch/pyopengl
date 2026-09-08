"""A Tk widget with an OpenGL context of its own.

:class:`GLFrame` is an ordinary ``tkinter.Frame`` that owns a GL context on its
own native window, so it packs, grids, resizes and is destroyed like any other
widget.  Nothing outside Python is involved: the context is made through the
window system's own API against the window handle Tk hands out.

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

**The context is made when the widget is mapped**, because a Tk window has no
native handle before that.  A program that wants to use GL straight after
building the widget -- to load textures, or because it drives its own loop --
calls :meth:`GLFrame.waitForMap`, which pumps Tk until the window is on screen
and the context exists.
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

#: How long :meth:`GLFrame.waitForMap` waits for the window system to put the
#: window on screen before giving up.  Long enough for a loaded machine, short
#: enough that a window that will never be mapped does not hang a program.
MAP_TIMEOUT = 5.0

#: How long one pass of the wait loop gives Tk before looking again.
MAP_POLL = 0.005


class GLFrame(tkinter.Frame):
    """A Tk frame that draws with OpenGL

    Subclass it and override :meth:`initgl` and :meth:`redraw`; everything else
    has a working default.

    The context attributes may be given as keywords -- ``profile``,
    ``version``, ``depthSize`` and the rest of
    :class:`~OpenGL.Tk.attributes.ContextAttributes` -- alongside the ordinary
    Tk options, or as a ready-made ``attributes``.  Anything else goes to
    ``tkinter.Frame`` as usual.

    Attributes:
        attributes -- what was asked of the context
        context -- the context object, or None before the widget is mapped;
            see :mod:`OpenGL.Tk.context` for what it answers
        contextError -- the failure that stopped a context being made, where
            one did.  Kept rather than raised out of the ``<Map>`` binding,
            where an exception would surface as a Tk callback error with no
            connection to the code that built the widget; :meth:`waitForMap`
            and :meth:`makeCurrent` raise it.
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
        # Tk paints a widget's background over whatever GL drew, which shows as
        # a flicker on every expose.  An empty background is Tk's own way of
        # saying "this widget draws itself".
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
        """Set up whatever this widget draws with

        Called once, with the context current, as soon as there is one.  It is
        where textures, shaders and buffers are made: before it there is no
        context to make them in, and it is not called again when the widget is
        resized or re-exposed.
        """

    def redraw(self) -> None:
        """Draw one frame

        Called with the context current; :meth:`render` swaps the buffers
        afterwards.
        """

    def reshape(self, width: int, height: int) -> None:
        """Follow the widget's new size

        The default sets the viewport to the whole widget, which is what a
        program that draws its own projection wants.  Called with the context
        current.
        """
        from OpenGL.GL import glViewport

        glViewport(0, 0, width, height)

    ### the context's life
    def createContext(self) -> Any:
        """Make this widget's GL context, if it has none yet

        Answers the context.  Raises
        :class:`~OpenGL.Tk.errors.TkContextError` where one cannot be had; the
        widget goes on working as an ordinary frame, so a program can catch it
        and offer something else.
        """
        if self.context is not None:
            return self.context
        # A context cannot be made while a glBegin block is open on the
        # current one, and a widget mapped from inside a redraw is exactly
        # where that happens.  See OpenGL.error.end_abandoned_block.
        end_abandoned_block()
        self.update_idletasks()         # so winfo_id() names a real window
        self.context = createContext(self, self.attributes)
        self.contextError = None
        log.debug('created %s', self.context.describe())
        return self.context

    def destroyContext(self) -> None:
        """Give this widget's context back

        Called for you when the widget is destroyed.  Calling it twice is
        calling it once.  Anything the context still holds -- textures,
        buffers, programs -- goes with it, so a program that caches GL names
        per context is told through PyOpenGL's own context tracking rather than
        from here.
        """
        self.stopAnimation()
        context, self.context = self.context, None
        if context is not None:
            context.destroy()
        self._initialised = False

    def waitForMap(self, timeout: float = MAP_TIMEOUT) -> Any:
        """Pump Tk until the window is on screen, and answer the context

        A Tk window has no native handle until the window system has mapped
        it, so there is nothing to make a context against before then.  This is
        how a program uses GL straight after building the widget rather than
        waiting for an event: it is what a script, a test and a program driving
        its own loop all want.

        Raises :class:`~OpenGL.Tk.errors.TkContextError` if the window is never
        mapped, or if making the context failed -- since a caller that asked
        for the context and did not get one has to be told, and the ``<Map>``
        binding is no place to raise from.
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
        """Draw into this widget from now on

        False where there is no context yet -- the widget is not mapped -- and
        raises where making one failed.
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

        Make current, :meth:`redraw`, swap.  A program driving its own loop
        calls this; the widget calls it for itself on expose and while an
        animation is running.
        """
        if not self.makeCurrent():
            return False
        self.redraw()
        self.swapBuffers()
        return True

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if it cannot

        One waits for the display and caps the frame rate at its refresh; zero
        draws as fast as the driver will, which is what a benchmark wants.
        """
        if self.context is None:
            return False
        return bool(self.context.setSwapInterval(interval))

    ### an animation, for a widget that is not driven from outside
    def startAnimation(self, interval: Optional[int] = None) -> None:
        """Render every ``interval`` milliseconds until told to stop

        For a widget whose scene changes on its own.  A program with a loop of
        its own calls :meth:`render` from it instead and leaves this alone.
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
                pass                    # the interpreter is already going

    def _animationStep(self) -> None:
        self._animationJob = None
        self.render()
        if self.animate > 0 and self.winfo_exists():
            self._animationJob = self.after(self.animate, self._animationStep)

    ### Tk bindings
    def _onMap(self, event: Any = None) -> None:
        """The window system has given this widget a window; take a context"""
        if self.context is not None:
            return
        try:
            self.createContext()
        except Exception as error:
            # Not raised: a Tk binding's exception surfaces as a callback error
            # with nothing to connect it to the code that built the widget.
            # waitForMap and makeCurrent raise it where a caller is listening.
            self.contextError = error
            log.error('could not make a GL context for %s: %s', self, error)
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
        """Part of the widget has been uncovered and wants drawing again"""
        if self.context is None:
            return
        self._ensureInitialised()
        self.render()

    def _onConfigure(self, event: Any = None) -> None:
        """Follow the widget's new size

        Only the size: ``initgl`` is *not* run again, since a resize does not
        make a new context and re-running it would rebuild every texture and
        shader each time somebody dragged a corner.
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
        """Let the context go with the widget"""
        if event is not None and event.widget is not self:
            return                      # a child's destruction, not ours
        self.destroyContext()

    ### the names the Togl-based widget answered to
    def tkRedraw(self, *arguments: Any) -> None:
        """Draw one frame; :meth:`render` under the name the old widget used"""
        self.render()

    def tkMakeCurrent(self) -> bool:
        """:meth:`makeCurrent`, under the name the old widget used"""
        return self.makeCurrent()

    def tkSwapBuffers(self) -> None:
        """:meth:`swapBuffers`, under the name the old widget used"""
        self.swapBuffers()
