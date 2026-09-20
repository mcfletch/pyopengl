# The documentation generators

The PyOpenGL documentation set is Sphinx, with its sources in `docs/`. Two of
its three parts are generated, and this directory holds the generators.

Build the whole set from the top of the checkout:

```
python build-docs.py
```

which fetches the Khronos sources, runs both generators, and calls Sphinx. The
result is in `docs/_build/html`. `python build-docs.py --help` covers the rest,
including `--stage` for a copy to look at and `--publish` for `gh-pages`, which
is what GitHub Pages serves.

## What each piece does

| File | Writes | From |
| --- | --- | --- |
| `acquireoriginal.py` | `OpenGL-Refpages/` | the Khronos reference-page repository |
| `generate.py` | `docs/reference/` | those DocBook sources, plus the installed packages |
| `dumbpydoc.py` | `docs/api/` | the installed packages |
| `rst.py` | -- | the DocBook-to-reStructuredText renderer both use |
| `model.py` | -- | the objects a reference entry is read into |
| `references.py`, `samples.py` | `.reference_cache.pkl` | source scans of other people's projects |

`docs/reference/` and `docs/api/` are not in version control: they are written
from the checkout each time, and `docs/.gitignore` says so.

## Cross-references

Each entry point is declared once in the whole set, and everything else links
to that declaration.

`generate.py` declares the Python entry points on the reference page for the
OpenGL command they wrap, with `py:function`, and records what it declared in
`docs/reference/entrypoints.json`. `dumbpydoc.py` reads that file: a name it
finds there is linked to its reference page rather than described again.

For everything else -- modules, classes, methods, attributes, constants, and
the entry points with no reference page, such as an extension's -- `dumbpydoc.py`
decides which module declares each name and declares it there in the Python
domain. A module that re-exports a name says which module declares it and how
many names it takes from there, rather than repeating the declaration. So
`:py:func:`OpenGL.GL.glBegin``, `:py:data:`GL_TRIANGLES`` and
`:py:mod:`OpenGL.arrays.vbo`` all resolve, each to one page, and each name
appears once in the index.

Which module declares a name comes from the `__module__` the declaration
tables record, which needs `MODULE_ANNOTATIONS`; `dumbpydoc.py` sets it before
importing anything.

`OpenGL.raw` gets no pages at all. There are no source files under it, only
declaration tables a finder turns into namespaces on demand, and every name in
it is exported by the module beside it -- which is where it is declared.

The reference is one directory and one index per API: `gl`, `gles1`, `gles2`,
`gles3`, `glu`, `glut`, `gle`, `glx`, `egl`, `wgl`. The same entry point can be
in several and mean something different in each, so each gets its own page, and
`entrypoints.json` is keyed by API package for the same reason. Khronos
publishes no reference pages for EGL or WGL, so those two indexes are built
from the packages instead. See `plans/SPHINX-DOCS.md`.

## Sample code references

`references.py` scans checkouts of other projects for calls to OpenGL entry
points and writes `.reference_cache.pkl`, which `generate.py` reads to add a
"Sample code references" section to each page. The scan wants the checkouts
`samples.py` fetches, and none of it is needed to build the set: without the
cache file the pages are written without those sections.

## Somebody else's set

`dumbpydoc.py` writes the module pages for any set of packages, not just this
one: `render_projects(projects, directory, entrypoints=None, title, paragraphs)`
takes the packages to document and where to put them, and the packages named
are also what a name has to come from to count as theirs -- anything imported
from outside them is linked rather than described. OpenGLContext's own set is
built that way, over the engine and the eight packages around it; its
`build-docs.py` calls this, and the commentary notation its tutorials are
written in lives in that repository.
