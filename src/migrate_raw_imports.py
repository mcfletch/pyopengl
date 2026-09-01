"""Rewrite the friendly modules to define their names rather than import them.

A friendly module used to say::

    from OpenGL.raw.GL.NV.gpu_shader5 import *
    from OpenGL.raw.GL.NV.gpu_shader5 import _EXTENSION_NAME

which built a module object and a dictionary in order to copy that dictionary
into this one.  It now says::

    from OpenGL._declarations import define as _define
    _EXTENSION_NAME = _define(globals(), 'OpenGL.raw.GL.NV.gpu_shader5')

The name in the string is what it always was, so it stays the identifier for
where a declaration came from, whether or not a file of that name exists.

Run from the package root::

    python src/migrate_raw_imports.py            # report what would change
    python src/migrate_raw_imports.py --write    # change it

It is idempotent: a module already migrated is left alone, so it can be run
again after new friendly modules are generated.
"""

import argparse
import os
import re
import sys

#: ``from OpenGL.raw.GL.NV.gpu_shader5 import *``
STAR = re.compile(r'^from (OpenGL\.raw\.[A-Za-z0-9_.]+) import \*[ \t]*$', re.M)

#: The line that follows it in every generated friendly module.
EXTENSION_NAME = 'from %s import _EXTENSION_NAME'

#: Bound under a private name, because ``from OpenGL.GL import *`` takes
#: whatever the friendly module has that is not private, and ``define`` is the
#: mechanism rather than something the module defines.
ASSIGNED = (
    'from OpenGL._declarations import define as _define\n'
    "_EXTENSION_NAME = _define(globals(), %r)"
)

#: For the few that never took ``_EXTENSION_NAME``: define the names, and do
#: not define one the module did not have.
BARE = 'from OpenGL._declarations import define as _define\n_define(globals(), %r)'


def rewrite(text):
    """The migrated source, or None where there is nothing to migrate."""
    match = STAR.search(text)
    if match is None:
        return None
    module = match.group(1)
    if STAR.search(text, match.end()) is not None:
        # Two generated modules feeding one friendly module: define() takes one
        # name, so this needs a person to look at it.
        return False
    # Most generated friendly modules take _EXTENSION_NAME on the next line;
    # a few never asked for it, and adding it would define a name the module
    # did not have.
    wanted = EXTENSION_NAME % (module,)
    takes_name = wanted in text
    replacement = (ASSIGNED if takes_name else BARE) % (module,)
    replaced = text[: match.start()] + replacement + text[match.end() :]
    return replaced.replace('\n' + wanted, '', 1)


def targets(root):
    """Friendly modules that take their names from a generated module."""
    for directory, folders, files in os.walk(os.path.join(root, 'OpenGL')):
        if 'raw' in directory.split(os.sep) or '__pycache__' in directory:
            folders[:] = [f for f in folders if f != '__pycache__']
            continue
        for name in sorted(files):
            if name.endswith('.py'):
                yield os.path.join(directory, name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='change the files')
    parser.add_argument('--root', default=os.getcwd())
    options = parser.parse_args(argv)

    changed, skipped = [], []
    for path in targets(options.root):
        with open(path, 'r', encoding='utf-8') as handle:
            text = handle.read()
        result = rewrite(text)
        if result is None:
            continue
        if result is False:
            skipped.append(path)
            continue
        changed.append(path)
        if options.write:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(result)
    print('%s %d modules' % ('rewrote' if options.write else 'would rewrite', len(changed)))
    for path in skipped:
        print('  needs a person: %s' % (os.path.relpath(path, options.root),))
    return 0


if __name__ == '__main__':
    sys.exit(main())
