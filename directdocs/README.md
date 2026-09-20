# The documentation generators

The PyOpenGL documentation set is Sphinx, with its sources in `docs/`. Two of
its three parts are generated, and this directory holds the generators.

Build the whole set from the top of the checkout:

```
python build-docs.py
```

which fetches the Khronos sources, runs both generators, and calls Sphinx. The
result is in `docs/_build/html`. `python build-docs.py --help` covers the rest,
including `--stage` for a copy to look at and `--publish` for the `htdocs`
branch.

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

## Sample code references

`references.py` scans checkouts of other projects for calls to OpenGL entry
points and writes `.reference_cache.pkl`, which `generate.py` reads to add a
"Sample code references" section to each page. The scan wants the checkouts
`samples.py` fetches, and none of it is needed to build the set: without the
cache file the pages are written without those sections.

## Commentary markup

The tutorial generator (`oglctutorials.py`) reads the `'''`-delimited strings in
a script as commentary and the code between them as samples. A blank line splits
the commentary into blocks, and each block is rendered according to how it
begins:

| Block | Rendered as |
| --- | --- |
| `=Heading=`, on one line | an `h1` |
| `_Heading_`, on one line | an `h2` |
| lines starting `*` or `-` | a bullet list |
| lines of the form `term -- definition` | a definition list |
| lines that line up under one another | a `pre`, with the spacing kept |
| anything else | a paragraph |

A block is indented in the output by the indent it has in the source.

Within a paragraph, `[target text]` is a link, or an image when the target ends
in `.png`, `.jpg`, `.bmp` or `.tif`. The target has to look like a location -- a
scheme, a path, an anchor, or a filename with an extension -- so bracketed prose
such as `[--help for the tunable knobs]` stays as it is written. A bare `http://`
or `https://` URL is linked where it stands.

Put `class=name` in front of the target to set the element's CSS class, which is
how a page floats one image against the next:

```
[class=clear-right transforms_1.py-screen-0009.png Perspective]
```

The classes available are the ones in the tutorial stylesheet, which is
`docs/style/tutorial.css` in OpenGLContext.

This generator writes HTML through Genshi templates and belongs to
OpenGLContext's documentation rather than to PyOpenGL's; it is the last thing
here that has not moved to Sphinx.
