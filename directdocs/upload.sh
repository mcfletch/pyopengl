#! /bin/bash

# relies on having the gh-pages checkout as `website`
# sitting next to the `pyopengl` root checkout
rsync -av manual-3.1/* ../../website/documentation/manual/
