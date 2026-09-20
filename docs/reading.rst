Learning OpenGL
===============

OpenGL from Python is OpenGL, so most of what has been written about OpenGL
applies whatever language the example is in.  This page collects the material
worth starting from.

Tutorials
---------

OpenGLContext
~~~~~~~~~~~~~

`OpenGLContext <https://github.com/mcfletch/openglcontext>`__ carries the
tutorial series written for PyOpenGL, as annotated source you can run.  It
teaches the OpenGL you would write today -- buffer objects, shaders,
framebuffer objects -- rather than the fixed-function pipeline.

The shader series runs from a first triangle to a scenegraph:

- **First steps** -- geometry in a vertex buffer object, a vertex and a
  fragment shader, and the draw call that uses them
- **Interpolated values** -- colour across a primitive
- **Uniform values** -- fog, and how a uniform reaches a shader
- **Attribute values** -- per-vertex data, and tweening between two meshes
- **Diffuse, ambient and directional lighting**, then **specular highlights
  with indexed geometry**
- **Multiple lights** -- GLSL arrays and structures, and then optimising the
  directional case
- **Point lights** and **spot-lights**
- **Declarative structures** and **shader scenegraph nodes** -- moving from a
  script that draws to a description of what to draw

Beyond it:

- **Instanced geometry** -- drawing many copies in one call, with texture
  buffer objects supplying the per-instance data
- **Shadows**, in three parts: depth comparison on the back buffer, the same
  thing in a framebuffer object, and then from the scenegraph
- **Particle systems**, **transforms**, **NURBS surfaces** and **text**

The engine's own source and documentation cover more: core-profile and
physically based rendering passes, a line-by-line walk through a PBR fragment
shader, levels of detail, overlay UI.

NeHe
~~~~

The `NeHe tutorials <http://nehe.gamedev.net/>`__ by Jeff Molofee are widely
recommended and worth knowing about, with one caveat that matters:

.. note::

   They teach **fixed-function OpenGL** -- ``glBegin``, ``glVertex``,
   ``glMatrixMode``, the fixed lighting model.  All of it is deprecated, none
   of it is in a core profile, and a program written that way today is
   writing against a compatibility path.  Read them for the ideas -- what a
   texture is, what a depth buffer does, how a frame is put together -- and
   write the code with buffer objects and shaders.

Python translations, if you want them:

- ``PyOpenGL-Demo/NeHe`` has tutorials 1 through 6, kept close to the original
  C so they read alongside the tutorial text.
- OpenGLContext's tests directory has ``nehe1.py`` through ``nehe8.py``,
  written for the result rather than the structure, plus ``glprint.py`` as a
  loose translation of 13.
- `Paul Furber's PyGame versions <https://www.pygame.org/gamelets/#NEHE>`__
  cover 1 through 10 in idiomatic, function-oriented Python.

Elsewhere
~~~~~~~~~

`Learn OpenGL <https://learnopengl.com/>`__ is a modern, shader-first course.
The code is C++, but the concepts and the GLSL carry over directly, and it is
the best free introduction to the pipeline as it now is.

Books
-----

*OpenGL Programming Guide* (the Red Book)
    The official guide.  Older editions are `widely available online
    <https://www.google.com/search?q=OpenGL+Programming+Guide>`__; the second
    edition covers OpenGL 1.1.  Addison-Wesley, ISBN 0-201-60458-2 for the
    third edition.

    Python versions of some of its tutorial code are in the ``redbook``
    directory of `PyOpenGL-Demo
    <https://github.com/mcfletch/pyopengl-demo>`__, kept close to the original
    source.

*OpenGL Shading Language* (the Orange Book)
    An introduction to shaders, from one-line shaders through emulating fixed
    function to non-photorealistic shading and caustics.  Adapting its code to
    a real scene is part of the work, but the grounding is sound.
    Addison-Wesley, ISBN 978-0-321-33489-3 for the second edition.

*OpenGL SuperBible*
    Covers OpenGL 1.0-era operations through to the 2.x model.  Older features
    get exhaustive coverage and newer ones less.  Sams, ISBN 0-672-32601-9 for
    the third edition.

Specifications and registries
-----------------------------

- `The OpenGL registry <https://registry.khronos.org/OpenGL/index_gl.php>`__ --
  the specifications, the header files and the XML PyOpenGL's bindings are
  generated from.
- `The extension registry
  <https://registry.khronos.org/OpenGL/extensions/>`__ -- what each extension
  means and what it declares.
- `Khronos' OpenGL reference pages
  <https://registry.khronos.org/OpenGL-Refpages/>`__ -- the upstream of the
  :doc:`reference pages <reference/index>` here.
- `MSDN's OpenGL documentation
  <https://learn.microsoft.com/en-us/windows/win32/opengl/opengl>`__, for WGL.

Other resources
---------------

- `OpenGL.org <https://www.opengl.org/>`__ -- specifications, documentation and
  the community around them.
- `LightHouse3D tutorials <https://www.lighthouse3d.com/tutorials/>`__ --
  intermediate material on particular OpenGL subjects.

Support
-------

Bug reports and feature requests go to the
`issue tracker <https://github.com/mcfletch/pyopengl/issues>`__.
