# PyOpenGL Direct Documentation Generator

To Produce the PyOpenGL documentation-set:

```
	./acquireoriginal.py
	./samples.py
	./references.py 
	./generate.py 
```

which will create a manual-X.Y directory and place the resulting HTML files
into it.

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
