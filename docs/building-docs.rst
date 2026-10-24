Building the documentation
==========================

``build-docs.py`` at the top of the checkout writes this documentation set:

.. code-block:: console

   $ pip install -e ".[docs]"
   $ python build-docs.py

The result is in ``docs/_build/html``.  The build writes a couple of thousand
pages, takes a few minutes, and ends with a summary of what it wrote.

What it is made of
------------------

Three parts, two of them generated:

``docs/*.rst``
    The narrative pages, written by hand.  This page is one of them.

``docs/reference/``
    The :doc:`reference pages <reference/index>`, written by
    ``directdocs/generate.py`` from the Khronos DocBook sources, with
    PyOpenGL's call signatures added to them.  The sources are two Khronos
    repositories, fetched into ``directdocs/`` by the build:
    `OpenGL-Refpages <https://github.com/KhronosGroup/OpenGL-Refpages>`__ for
    OpenGL, OpenGL ES, GLU and GLX, and the ``sdk/docs/man`` directory of
    `EGL-Registry <https://github.com/KhronosGroup/EGL-Registry>`__ for EGL.
    Khronos builds its own HTML from the same sources with the DocBook XSL
    toolchain its `README
    <https://github.com/KhronosGroup/OpenGL-Refpages/blob/main/README.adoc>`__
    lists; ``generate.py`` reads the DocBook with lxml and needs none of it.

``docs/api/``
    The :doc:`API pages <api/index>`, written by ``directdocs/dumbpydoc.py``.
    It imports the packages and inspects their contents.  Most of PyOpenGL's
    exports have no ``def`` in the source.  They are built at import time from
    the declaration tables, so importing is the only way to list them.

The two generated directories are not in version control.  ``directdocs/README.md``
describes each generator, and ``plans/SPHINX-DOCS.md`` records how the set is
put together and why.

Running one part at a time
--------------------------

.. code-block:: console

   $ python build-docs.py --only html          # just Sphinx, on what is there
   $ python build-docs.py --only api --only html
   $ python build-docs.py --no-fetch           # do not pull the Khronos sources

``--skip OpenGL.raw`` (and the same flag with other packages) leaves a subtree
out of the API pages, so a change can be previewed without building the whole
set.  ``-W`` turns Sphinx's warnings into errors, as CI requires.

The usage references
--------------------

Each reference page can list source code that calls the entry point it
describes, as examples of how the entry point is used.  The list is built by
scanning checkouts of other people's projects:

.. code-block:: console

   $ python directdocs/samples.py      # fetch the projects, into directdocs/.samples
   $ python directdocs/references.py   # scan them, writing .reference_cache.pkl

Both take a while.  Neither is needed to build the set: without the cache
file, the pages are written without their sample sections.  ``build-docs.py
--samples`` does the pair as part of a build.

Publishing
----------

.. code-block:: console

   $ python build-docs.py --stage ../preview    # a copy to look at
   $ python build-docs.py --publish             # onto the gh-pages branch
   $ python build-docs.py --publish --push      # and send it to the remote

Publishing writes through git's plumbing commands without checking the branch
out, so it never touches the working tree.  It replaces ``gh-pages`` with a
single commit that has no parent, so the repository holds one copy of the site
instead of one per release.  Replacing the branch needs a forced push.  The
push uses a lease taken before the build starts, so if someone else publishes
during the build, this push is refused and their publish is kept.

``.github/workflows/documentation.yml`` runs the build when it is started by
hand, once a release has settled.  It publishes only when its ``publish``
input is ticked.
Nothing leaves the machine without ``--push``.

``python build-docs.py --help`` has the rest.
