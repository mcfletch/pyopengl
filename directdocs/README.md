# The documentation generators

The PyOpenGL documentation set is Sphinx, with its sources in `docs/`. Two of
its three parts are generated, and this directory holds the generators.

Build the whole set from the top of the checkout:

```
python build-docs.py
```

This fetches the Khronos sources, runs both generators, and calls Sphinx. The
result is in `docs/_build/html`. `python build-docs.py --help` covers the other
options, including `--stage` to write a preview copy and `--publish` to write
the `gh-pages` branch that GitHub Pages serves.

## What each piece does

| File | Writes | From |
| --- | --- | --- |
| `acquireoriginal.py` | `OpenGL-Refpages/`, `EGL-Registry/` | the two Khronos repositories the reference pages are in |
| `generate.py` | `docs/reference/` | those DocBook sources, plus the installed packages |
| `dumbpydoc.py` | `docs/api/` | the installed packages |
| `rst.py` | (nothing) | the DocBook-to-reStructuredText renderer both use |
| `model.py` | (nothing) | the objects a reference entry is read into |
| `references.py`, `samples.py` | `.reference_cache.pkl` | source scans of other people's projects |

`docs/reference/` and `docs/api/` are not in version control. They are written
from the checkout on each build, and `docs/.gitignore` lists them.

## Cross-references

Each entry point is declared once in the whole set, and everything else links
to that declaration.

`generate.py` declares the Python entry points on the reference page for the
OpenGL command they wrap, with `py:function`. It records each declaration in
`docs/reference/entrypoints.json`. `dumbpydoc.py` reads that file and links
each name listed there to its reference page, without describing it again.

Everything else is declared by `dumbpydoc.py`: modules, classes, methods,
attributes, constants, and entry points with no reference page (such as an
extension's). It finds the module that declares each name and declares the name
there in the Python domain. The page for a module that re-exports names gives
the declaring module and the number of names taken from it, without repeating
the declarations. So
`:py:func:`OpenGL.GL.glBegin``, `:py:data:`GL_TRIANGLES`` and
`:py:mod:`OpenGL.arrays.vbo`` all resolve, each to one page, and each name
appears once in the index.

Which module declares a name comes from the `__module__` the declaration
tables record, which needs `MODULE_ANNOTATIONS`; `dumbpydoc.py` sets it before
importing anything.

### How a docstring is read

A docstring that uses a role (`:class:`), a literal (` ``name`` `), a
directive, or a Sphinx info field (`:param name:`, `:raises Error:`) is
reStructuredText, and is written into the page unchanged, with one exception.
A run of `name -- description` lines becomes a definition list. A code sample
in such a docstring therefore needs `::` to introduce it, and `|` needs a
literal around it.

Any other docstring is plain text. Its prose is escaped, so an asterisk is an
asterisk, and it is read as:

- `name -- description` lines, as a definition list. Several names share an
  entry as `a, b` or `a/b`, and a note in brackets stays with them:
  `separable (keyword only) -- ...`. A description wraps onto indented lines,
  and entries indented under one are a list of their own.
- Lines starting `- `, `* ` or `+ `, as a bulleted list.
- An indented block, as a literal block, with the `::` introducing it taken
  off the paragraph above.

`tests/directdocs/test_rst.py` holds each of these to reStructuredText that
docutils reads without a warning.

`OpenGL.raw` gets no pages. It has no source files, only declaration tables
that an import finder turns into namespaces on demand. Every name in it is
exported by the matching non-raw module, and is declared on that module's page.

The reference is one directory and one index per API: `gl`, `gles1`, `gles2`,
`gles3`, `glu`, `glut`, `gle`, `glx`, `egl`, `wgl`. The same entry point can
appear in several APIs with a different meaning in each. Each API therefore has
its own page for it, and `entrypoints.json` is keyed by API package. The EGL pages
are the EGL 1.5 set in EGL-Registry's `sdk/docs/man`; every other Khronos page
is from OpenGL-Refpages. Khronos publishes no reference pages for WGL, so its
index is built from the package instead. See `plans/SPHINX-DOCS.md`.

## Sample code references

`references.py` scans checkouts of other projects for calls to OpenGL entry
points and writes `.reference_cache.pkl`. `generate.py` reads that file to add
a "Sample code references" section to each page. The scan reads the checkouts
that `samples.py` fetches. Neither step is needed to build the set: without the
cache file, the pages are written without those sections.

## Somebody else's set

`dumbpydoc.py` can write module pages for any set of packages.
`render_projects(projects, directory, entrypoints=None, title, paragraphs)`
takes the packages to document and the output directory. Only names defined in
those packages are described. A name imported from outside them is linked to
its own documentation. OpenGLContext's documentation set covers the engine and
the eight packages around it, and its `build-docs.py` calls `render_projects`.
The commentary notation its tutorials use is defined in the OpenGLContext
repository.
