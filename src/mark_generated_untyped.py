#! /usr/bin/env python
"""Tell a type checker not to analyse the generated modules.

``py.typed`` is a promise that the package can be analysed, and downstream
checkers keep it: a user's own report fills with errors from files they never
wrote.  The generated modules cannot honour that promise and should not
pretend to -- their names arrive from the declaration tables when
``define()`` runs, so a checker reading the source sees a module that defines
almost nothing and calls a great many things that are "not defined".

What *is* the typed surface is the ``.pyi`` stub beside each package, which
says what every entry point takes and returns.  This marks the generated
source as out of scope so the stubs are what a checker uses.

    python src/mark_generated_untyped.py --write
"""

import argparse
import os
import sys

MARKER = '# mypy: ignore-errors\n'

REASON = (
    '# The names in this module arrive from the declaration tables at import\n'
    '# time, so a checker reading this file sees calls to things it cannot\n'
    '# find.  The typed surface is the .pyi stub beside the package.\n'
)


def generated(path, text):
    """Whether this file is machine-written rather than authored."""
    if os.sep + 'raw' + os.sep in path:
        return True
    return '_define(globals()' in text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--root', default='OpenGL')
    options = parser.parse_args(argv)

    marked = 0
    for directory, folders, files in os.walk(options.root):
        if '__pycache__' in directory:
            continue
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            with open(path, 'r', encoding='utf-8') as handle:
                text = handle.read()
            if not generated(path, text) or text.startswith(MARKER):
                continue
            marked += 1
            if options.write:
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write(MARKER + REASON + text)
    print('%s %d generated modules' % ('marked' if options.write else 'would mark', marked))
    return 0


if __name__ == '__main__':
    sys.exit(main())
