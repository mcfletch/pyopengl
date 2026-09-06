"""Choosing the way a GL context is made for a Tk widget.

The choice is made from **Tk's own** answer to ``tk windowingsystem`` rather
than from :data:`sys.platform`, because they can differ and Tk's is the one
that matters: an X11 build of Tk running on macOS through XQuartz has X windows
and wants GLX, and asking ``sys.platform`` there would send it to a Cocoa
implementation for windows that are not Cocoa's.

A context object -- whichever this returns -- answers:

``makeCurrent()``
    draw into this widget from now on; False if the driver refused
``releaseCurrent()``
    let go, leaving no context current
``swapBuffers()``
    show what has been drawn
``setSwapInterval(n)``
    wait n refreshes between swaps; False where the driver offers no way
``destroy()``
    give the context back; calling it twice is calling it once
``describe()``
    one line, for a log message
``handle``
    the platform's own context handle
"""

from __future__ import annotations

from typing import Any, Optional

from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.errors import TkContextError

__all__ = ['createContext', 'windowingSystem']

#: What each of Tk's windowing systems is served by.  ``aqua`` is absent, and
#: :func:`createContext` says what that costs.
IMPLEMENTATIONS = {
    'x11': ('OpenGL.Tk.glx', 'GLXContext'),
    'win32': ('OpenGL.Tk.win32', 'WGLContext'),
}

#: What to tell somebody on macOS, where a context is attached to a view
#: through Objective-C rather than by a call taking a window id.
AQUA_MESSAGE = (
    'OpenGL.Tk has no context implementation for Tk on Aqua yet: a context is '
    'attached to an NSView there, through Objective-C, rather than made '
    'against a window id. Togl (OpenGL.Tk.togl) and the pyopengltk package '
    'both cover it meanwhile, and an X11 build of Tk on macOS is served by the '
    'GLX implementation here.'
)


def windowingSystem(widget: Any) -> str:
    """Which windowing system Tk is using: ``x11``, ``win32`` or ``aqua``"""
    return str(widget.tk.call('tk', 'windowingsystem'))


def createContext(
    widget: Any, attributes: Optional[ContextAttributes] = None
) -> Any:
    """A GL context on ``widget``'s native window

    widget -- a mapped Tk widget; a window has no native handle before it is
        mapped, so this is called from the widget's ``<Map>`` binding
    attributes -- a :class:`~OpenGL.Tk.attributes.ContextAttributes`, or None
        for the defaults

    Raises :class:`~OpenGL.Tk.errors.TkContextError` where no context can be
    had, saying which of the reasons it was.
    """
    attributes = attributes or ContextAttributes()
    system = windowingSystem(widget)
    if system == 'aqua':
        raise TkContextError(AQUA_MESSAGE)
    named = IMPLEMENTATIONS.get(system)
    if named is None:
        raise TkContextError(
            'OpenGL.Tk does not know the %r windowing system; it serves %s'
            % (system, ', '.join(sorted(IMPLEMENTATIONS))))
    moduleName, className = named
    module = __import__(moduleName, {}, {}, [className])
    return getattr(module, className)(widget, attributes)
