OpenGL in a Tkinter widget
==========================

``OpenGL.Tk.GLFrame`` is an ordinary ``tkinter.Frame`` that owns an OpenGL context on its own native window. It packs, grids, resizes and is destroyed like any other widget, and it needs nothing outside Python: Tk hands out the platform's window handle and the context is made against it through the window system's own API.

::

   import tkinter
   from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor
   from OpenGL.Tk import GLFrame

   class Scene(GLFrame):
       def initgl(self):                  # once, with the context current
           glClearColor(0.2, 0.3, 0.3, 1.0)

       def redraw(self):                  # per frame
           glClear(GL_COLOR_BUFFER_BIT)

   root = tkinter.Tk()
   Scene(root, width=640, height=480).pack(fill='both', expand=True)
   root.mainloop()

``examples/tk_shader.py`` in the source distribution is a longer one: a shaded triangle through a GLSL 3.30 program, a vertex array object and a uniform matrix, in a window beside ordinary Tk widgets.

The context is a core profile by default
----------------------------------------

What the context is asked for is ``OpenGL.Tk.ContextAttributes`` — profile, version, buffer sizes, multisampling, stereo, a debug context, a context to share with — given either as keywords to the widget or as a ready-made object:

::

   frame = GLFrame(root, width=640, height=480,
                   profile='core', version=(4, 1),
                   depthSize=24, samples=4)

The default is OpenGL 3.3 core, so shaders and vertex array objects are available without asking. ``profile='compatibility'`` keeps the fixed-function pipeline; ``profile='legacy'`` asks for no version and no profile at all, which is the only thing a driver without ``ARB_create_context`` will answer.

A profile is a GL 3.2 idea, so a request naming a version below that is sent without one — a driver handed a profile mask for GL 2.1 refuses the whole request rather than ignoring the part of it that means nothing.

The context arrives when the window does
----------------------------------------

A Tk window has no native handle until the window system has mapped it, so there is nothing to make a context against before then. The widget makes one from its ``<Map>`` binding and runs ``initgl``; a program that wants to use GL straight after building the widget — to load textures, or because it drives its own loop — asks for it:

::

   frame = Scene(root, width=640, height=480)
   frame.pack()
   frame.waitForMap()                     # pumps Tk until there is a context
   frame.render()                         # make current, redraw, swap

``initgl`` runs **once**. A resize sets the viewport and redraws; it does not run ``initgl`` again, which would rebuild every texture and shader each time somebody dragged a corner.

``startAnimation(milliseconds)`` renders on a timer for a scene that changes on its own; a program with a loop of its own calls ``render()`` from it and leaves the timer alone.

When a context cannot be had
----------------------------

Making one can fail for ordinary reasons: a driver without ``ARB_create_context``, a version it will not give, eight multisample samples nobody offers. The widget raises ``OpenGL.Tk.TkContextError``, and goes on working as an ordinary frame, so a program can catch it and offer something else.

::

   from OpenGL.Tk import GLFrame, TkContextError

   frame = Scene(root, version=(4, 6))
   frame.pack()
   try:
       frame.waitForMap()
   except TkContextError as error:
       fallBackToSomethingElse(error)

The failure arrives from ``waitForMap()`` or ``makeCurrent()`` rather than out of the ``<Map>`` binding, where an exception would surface as a Tk callback error with nothing to connect it to the code that built the widget.

Which platforms
---------------

+---------------------+-------------------------------------------------------------------+------------------------------+
| Tk windowing system | How                                                               | State                        |
+=====================+===================================================================+==============================+
| ``x11``             | ``glXCreateContextAttribsARB`` on the window ``winfo_id()`` names | Implemented                  |
+---------------------+-------------------------------------------------------------------+------------------------------+
| ``win32``           | ``wglCreateContextAttribsARB`` on that window's device context    | Implemented                  |
+---------------------+-------------------------------------------------------------------+------------------------------+
| ``aqua``            | ``NSOpenGLContext.setView:`` on the ``NSView`` Tk owns            | Raises, naming what it needs |
+---------------------+-------------------------------------------------------------------+------------------------------+

The choice is made from Tk's own ``tk windowingsystem`` rather than from ``sys.platform``, so an X11 build of Tk on macOS gets GLX and is right.

More than one context
---------------------

Several widgets in one program each get a context of their own, and ``makeCurrent()`` says which one you are drawing into. PyOpenGL resolves entry points per context, so it has to be told which is current; ``GLFrame`` tells it, for its own context and for the throwaway ones WGL needs to look its extensions up through. **You do not call ``OpenGL.dispatch.make_current`` or ``forget_context`` for a widget's context** — only for a context you made yourself, through some other toolkit.

A widget also closes a ``glBegin`` block left open on its context before destroying it, since a context destroyed inside one is undefined and a driver need not survive it. Your own ``redraw`` should still close its blocks: ``glBegin(...)`` then ``try: ... finally: glEnd()``.

Togl, and the widgets that used it
----------------------------------

``OpenGL.Tk`` was a wrapper around `Togl <http://togl.sourceforge.net/>`__, a Tcl C extension that has to be installed separately. ``Togl``, ``RawOpengl`` and ``Opengl`` keep their names, their constructors and their methods, and Togl's own widget options go on meaning what they meant:

::

   viewer = Opengl(root, width=400, height=400, double=1, depth=1)
   viewer.redraw = drawTheScene
   viewer.pack(fill='both', expand=True)

What changed underneath is that ``RawOpengl`` and ``Opengl`` are ``GLFrame`` subclasses and need no Tcl extension. They draw with the fixed-function pipeline — ``glMatrixMode``, ``gluPerspective``, ``glLightfv`` — so they ask for a compatibility profile. ``Togl`` itself still needs Togl, and loads it the first time one is made rather than when the module is imported.

Importing ``OpenGL.Tk`` now opens no window, needs no display and loads no Tcl package.
