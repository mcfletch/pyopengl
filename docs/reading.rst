Learning OpenGL
===============

OpenGL from Python is OpenGL, so most of what has been written about OpenGL
applies whatever language the example is in.  This page collects the material
worth starting from.

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

Tutorials
---------

The `NeHe tutorials <http://nehe.gamedev.net/>`__ by Jeff Molofee run from
opening a window to particle systems, scene loading, video textures, text,
morphing and multitexturing.  The older ones describe fixed-function OpenGL,
which is worth knowing while reading them.

Python translations:

- ``PyOpenGL-Demo/NeHe`` has tutorials 1 through 6, with a multitextured
  variant of 6.  These follow the original C structure closely, which makes
  them easier to read alongside the tutorial text than as Python.
- `Paul Furber's PyGame versions
  <https://www.pygame.org/gamelets/#NEHE>`__ are direct translations in
  idiomatic, function-oriented Python, covering tutorials 1 through 10.
- `OpenGLContext <https://github.com/mcfletch/openglcontext>`__ has ``nehe*.py``
  in its tests directory: translations written for the result rather than the
  structure, using object-oriented Python and OpenGLContext's own scenegraph.
  Tutorials 1 through 8 are translated, and ``glprint.py`` is a loose
  translation of 13, bitmapped text.

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
- `Learn OpenGL <https://learnopengl.com/>`__ -- a modern, shader-first course;
  the code is C++ but the concepts and the GLSL carry over directly.

Support
-------

Bug reports and feature requests go to the
`issue tracker <https://github.com/mcfletch/pyopengl/issues>`__.
