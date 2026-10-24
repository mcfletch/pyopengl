"""Select the GL context implementation for a Tk widget.

The implementation is chosen from Tk's ``tk windowingsystem`` result rather
than from :data:`sys.platform`, because the two can differ.  An X11 build of Tk
running on macOS through XQuartz creates X windows and needs GLX.
``sys.platform`` would select the Cocoa implementation for those windows.

Every context object returned here provides:

``makeCurrent()``
    make this widget's context current; False if the driver refused
``releaseCurrent()``
    leave no context current
``swapBuffers()``
    show what has been drawn
``setSwapInterval(n)``
    wait n refreshes between swaps; False where the driver has no way to set it
``destroy()``
    release the context; a second call does nothing
``describe()``
    one line, for a log message
``handle``
    the platform's own context handle
"""

from __future__ import annotations

from typing import Any, Optional

from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.errors import TkContextError

__all__ = ['createContext', 'gone', 'nowCurrent', 'windowingSystem']


def nowCurrent(handle: object) -> None:
    """Record ``handle`` as the context current on this thread.

    The dispatch layer keys its table of resolved entry points by context
    handle.  The driver reuses handle addresses.  The implementations here also
    create contexts the application never sees.  WGL creates two temporary
    contexts per widget, because ``wglChoosePixelFormatARB`` and
    ``wglCreateContextAttribsARB`` can only be looked up through an existing
    context.  Their addresses are often reused for the widget's own context.

    ``OpenGL.Tk`` creates these contexts, so it reports each switch itself.  A
    program using :class:`~OpenGL.Tk.widget.GLFrame` does not need to call
    ``OpenGL.dispatch.make_current``.
    """
    from OpenGL import _dispatch

    _dispatch.make_current(handle)


def gone(handle: object) -> None:
    """Retire the dispatch table for ``handle`` before the context is destroyed.

    A later context given the same address then resolves its own entry points.
    Without this call it would use the destroyed context's table, which can
    report an entry point as undefined when the new context has it, or as
    resolved when it does not.
    """
    from OpenGL import _dispatch

    _dispatch.forget_context(handle)

#: What each of Tk's windowing systems is served by.
IMPLEMENTATIONS = {
    'x11': ('OpenGL.Tk.glx', 'GLXContext'),
    'win32': ('OpenGL.Tk.win32', 'WGLContext'),
    'aqua': ('OpenGL.Tk.aqua', 'AquaContext'),
}


def windowingSystem(widget: Any) -> str:
    """Which windowing system Tk is using: ``x11``, ``win32`` or ``aqua``"""
    return str(widget.tk.call('tk', 'windowingsystem'))


def createContext(
    widget: Any, attributes: Optional[ContextAttributes] = None
) -> Any:
    """A GL context on ``widget``'s native window

    widget - a mapped Tk widget; a window has no native handle before it is
        mapped, so this is called from the widget's ``<Map>`` binding
    attributes - a :class:`~OpenGL.Tk.attributes.ContextAttributes`, or None
        for the defaults

    Raises :class:`~OpenGL.Tk.errors.TkContextError` when no context can be
    created.  The message gives the reason.
    """
    attributes = attributes or ContextAttributes()
    system = windowingSystem(widget)
    named = IMPLEMENTATIONS.get(system)
    if named is None:
        raise TkContextError(
            'OpenGL.Tk does not know the %r windowing system; it serves %s'
            % (system, ', '.join(sorted(IMPLEMENTATIONS))))
    moduleName, className = named
    module = __import__(moduleName, {}, {}, [className])
    return getattr(module, className)(widget, attributes)
