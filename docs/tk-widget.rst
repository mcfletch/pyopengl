OpenGL in a Tkinter widget
==========================

``OpenGL.Tk.GLFrame`` is an ordinary ``tkinter.Frame`` that owns an OpenGL context on its own native window. It packs, grids, resizes and is destroyed like any other widget. It needs nothing outside Python. Tk supplies the platform's native window handle, and ``GLFrame`` creates the context on that window through the window system's own API (GLX, WGL or NSOpenGL, listed under `Which platforms`_).

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

``examples/tk_shader.py`` in the source distribution is a longer example. It draws a shaded triangle with a GLSL 3.30 program, a vertex array object and a uniform matrix, in a window beside ordinary Tk widgets.

The context is a core profile by default
----------------------------------------

``OpenGL.Tk.ContextAttributes`` describes the context to request: profile, version, buffer sizes, multisampling, stereo, a debug context, and a context to share with. Pass these as keywords to the widget, or pass a ready-made ``ContextAttributes`` object:

::

   frame = GLFrame(root, width=640, height=480,
                   profile='core', version=(4, 1),
                   depthSize=24, samples=4)

The default is OpenGL 3.3 core, so shaders and vertex array objects are available without extra options. ``profile='compatibility'`` keeps the fixed-function pipeline. ``profile='legacy'`` requests no version and no profile. A driver without ``ARB_create_context`` accepts only that request.

Profiles were introduced in GL 3.2. A request for a version below 3.2 is sent without a profile, because a driver given a profile mask for GL 2.1 rejects the whole request.

The context arrives when the window does
----------------------------------------

A Tk window has no native handle until the window system maps it, so no context can be created before then. The widget creates the context from its ``<Map>`` binding and then runs ``initgl``. A program that needs GL straight after building the widget (to load textures, or because it runs its own loop) calls ``waitForMap()``:

::

   frame = Scene(root, width=640, height=480)
   frame.pack()
   frame.waitForMap()                     # pumps Tk until there is a context
   frame.render()                         # make current, redraw, swap

``initgl`` runs **once**. A resize sets the viewport and redraws. It does not run ``initgl`` again, because that would rebuild every texture and shader on each resize.

``startAnimation(milliseconds)`` renders on a timer, for a scene that changes over time. A program with its own loop calls ``render()`` from that loop and does not start the timer.

When context creation fails
---------------------------

Context creation can fail for ordinary reasons: a driver without ``ARB_create_context``, a version the driver does not support, or a sample count (such as 8) that no pixel format offers. The widget then raises ``OpenGL.Tk.TkContextError`` and keeps working as an ordinary frame. A program can catch the error and fall back to something else.

::

   from OpenGL.Tk import GLFrame, TkContextError

   frame = Scene(root, version=(4, 6))
   frame.pack()
   try:
       frame.waitForMap()
   except TkContextError as error:
       fallBackToSomethingElse(error)

The error is raised from ``waitForMap()`` or ``makeCurrent()``. It is not raised from the ``<Map>`` binding, because there it would appear as a Tk callback error with no link to the code that built the widget.

Which platforms
---------------

+---------------------+-------------------------------------------------------------------+------------------------------+
| Tk windowing system | How                                                               | State                        |
+=====================+===================================================================+==============================+
| ``x11``             | ``glXCreateContextAttribsARB`` on the window ``winfo_id()`` names | Implemented                  |
+---------------------+-------------------------------------------------------------------+------------------------------+
| ``win32``           | ``wglCreateContextAttribsARB`` on that window's device context    | Implemented                  |
+---------------------+-------------------------------------------------------------------+------------------------------+
| ``aqua``            | ``NSOpenGLContext.setView:`` on a view over the widget            | Implemented                  |
+---------------------+-------------------------------------------------------------------+------------------------------+

The platform is chosen from Tk's own ``tk windowingsystem`` value, not from ``sys.platform``. An X11 build of Tk on macOS therefore gets GLX, which is correct for that build.

Tk on macOS
-----------

Tk's Aqua widgets are rectangles drawn into the one ``NSView`` that fills each toplevel window. Individual widgets have no window id to create a context on. ``GLFrame`` therefore adds its own ``NSView`` to the toplevel's content view and keeps it over the widget's rectangle as the widget and its toplevel move and resize. It hides the view while the widget is unmapped, and attaches an ``NSOpenGLContext`` to it. ``OpenGL.CGL`` (CGL is the lowest-level OpenGL interface on macOS) chooses the pixel format and the profile. It prefers a GPU renderer, and uses Apple's CPU renderer on a machine without one.

* The view is drawn above Tk's own widgets. A Tk widget placed over a ``GLFrame`` is hidden behind it.
* The surface is the widget's size in points. On a Retina display the system scales it up, so ``glViewport(0, 0, winfo_width(), winfo_height())`` stays correct.
* macOS provides OpenGL up to 4.1. A core profile is 3.2 to 4.1. Fixed-function drawing needs ``profile='legacy'``, or ``profile='compatibility'`` with ``version=None``, and gets a 2.1 context. ``profile='compatibility'`` with a version above 2.1 raises ``TkContextError``, as does any version above 4.1. macOS pixel formats have no debug attribute, so ``debug=True`` creates an ordinary context there, without ``GL_KHR_debug`` reporting.
* A context below the version its profile requires (for example, on a machine whose only renderer implements 2.1) raises ``TkContextError`` instead of being returned. The first 3.x call on such a context would end the process.
* The swap interval is 0 unless ``swapInterval`` sets it. The window server already composites a windowed context and synchronises it to the display. An interval of 1 on top of that waits for a display refresh, which never arrives on a machine without a display.
* ``frame.context.profile`` and ``frame.context.renderer`` give the CGL profile and the renderer kind (``accelerated``, ``any`` or ``software``) that were used.
* The Objective-C calls are made through ``ctypes``, so no extra package is needed.

More than one context
---------------------

Several widgets in one program each get their own context, and ``makeCurrent()`` selects the one you draw into. PyOpenGL resolves entry points per context, so it must be told which context is current. ``GLFrame`` tells it, both for its own context and for the temporary contexts WGL needs to look up its extensions. You do not call ``OpenGL.dispatch.make_current`` or ``forget_context`` for a widget's context. Call them only for a context you created yourself, through some other toolkit.

Before a widget destroys its context, it closes any ``glBegin`` block left open on that context. Destroying a context inside a ``glBegin`` block is undefined behaviour, and a driver may crash. Your own ``redraw`` should still close its blocks: ``glBegin(...)`` then ``try: ... finally: glEnd()``.

Togl, and the widgets that used it
----------------------------------

``OpenGL.Tk`` was a wrapper around `Togl <http://togl.sourceforge.net/>`__, a Tcl C extension that has to be installed separately. ``Togl``, ``RawOpengl`` and ``Opengl`` keep their names, constructors and methods. Togl's own widget options keep their meanings:

::

   viewer = Opengl(root, width=400, height=400, double=1, depth=1)
   viewer.redraw = drawTheScene
   viewer.pack(fill='both', expand=True)

``RawOpengl`` and ``Opengl`` are ``GLFrame`` subclasses and need no Tcl extension. They draw with the fixed-function pipeline (``glMatrixMode``, ``gluPerspective``, ``glLightfv``), so they request a compatibility profile. ``Togl`` itself still needs the Togl extension. It loads the extension when the first ``Togl`` widget is created, not when the module is imported.

Importing ``OpenGL.Tk`` opens no window, needs no display and loads no Tcl package.
