Building the documentation
==========================

``build-docs.py`` at the top of the checkout writes this documentation set:

.. code-block:: console

   $ pip install -e ".[docs]"
   $ python build-docs.py

The result is in ``docs/_build/html``.  It takes a few minutes -- there are a
couple of thousand pages -- and ends with a summary of what it wrote.

What it is made of
------------------

Three parts, two of them generated:

``docs/*.rst``
    The narrative pages, written by hand.  This page is one of them.

``docs/reference/``
    The :doc:`reference pages <reference/index>`, written by
    ``directdocs/generate.py`` from the Khronos DocBook sources, with
    PyOpenGL's call signatures added to them.

``docs/api/``
    The :doc:`API pages <api/index>`, written by ``directdocs/dumbpydoc.py`` by
    importing the packages and looking at what they hold -- which is the only
    way to see what PyOpenGL exports, since most of it is built at import time
    from the declaration tables rather than written out as ``def``.

The two generated directories are not in version control.  ``directdocs/README.md``
describes each generator, and ``plans/SPHINX-DOCS.md`` records how the set is
put together and why.

Running one part at a time
--------------------------

.. code-block:: console

   $ python build-docs.py --only html          # just Sphinx, on what is there
   $ python build-docs.py --only api --only html
   $ python build-docs.py --no-fetch           # do not pull the Khronos sources

``--skip OpenGL.raw`` and friends leave a subtree out of the API pages, which
is how to get a look at a change without waiting for the whole set.
``-W`` turns Sphinx's warnings into errors, which is what CI wants.

The usage references
--------------------

Each reference page can list source code that calls the entry point it
describes, which is often the fastest way to see how one is used in practice.
That list is built by scanning checkouts of other people's projects:

.. code-block:: console

   $ python directdocs/samples.py      # fetch the projects, into directdocs/.samples
   $ python directdocs/references.py   # scan them, writing .reference_cache.pkl

Both take a while and neither is needed to build the set: without the cache
file the pages are written without their sample sections.  ``build-docs.py
--samples`` does the pair as part of a build.

Publishing
----------

.. code-block:: console

   $ python build-docs.py --stage ../preview    # a copy to look at
   $ python build-docs.py --publish             # onto the gh-pages branch
   $ python build-docs.py --publish --push      # and send it to the remote

Publishing writes through git's plumbing rather than checking the branch out,
so it never touches the working tree, and it replaces ``gh-pages`` with a
single commit that has no parent -- the repository then carries one copy of the
site rather than one per release.  That means a forced push, made against a
lease taken before the build starts, so a publish from somewhere else during
those minutes is refused rather than lost.

``.github/workflows/documentation.yml`` does this on a push to ``master``.
Nothing leaves the machine without ``--push``.

``python build-docs.py --help`` has the rest.
