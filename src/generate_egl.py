#! /usr/bin/env python
"""Generate the EGL bindings the registry declares and the tree lacks.

Khronos publishes EGL separately from OpenGL, and nothing here read it until
now, so the tree carried 117 of the 158 commands.  This writes the rest::

    python src/fetch_registries.py      # get egl.xml
    python src/generate_egl.py          # write what is missing
    python src/regenerate_c.py          # and rebuild the tables from it

It writes only what is absent, so running it again after a registry update
adds the new entry points and touches nothing else.  ``--dry-run`` says what
it would write.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from cdispatch import eglgen  # noqa: E402

EGL_XML = os.path.join(HERE, 'eglapi', 'api', 'egl.xml')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', default=os.path.join(ROOT, 'OpenGL'))
    parser.add_argument('--registry', default=EGL_XML)
    parser.add_argument('--dry-run', action='store_true')
    options = parser.parse_args(argv)

    if not os.path.exists(options.registry):
        print('no EGL registry at %s; run python src/fetch_registries.py'
              % (options.registry,))
        return 1

    registry = eglgen.read(options.registry)
    undefined = eglgen.undefined_types(registry, options.package)
    if undefined:
        # A wrong type is a crash in somebody's driver, so this stops rather
        # than guessing.  Add them to OpenGL/raw/EGL/_types.py.
        print('these types are named by the registry and not defined:')
        for name in sorted(undefined):
            print('   ', name)
        return 1

    missing = eglgen.missing_commands(registry, options.package)
    if not missing:
        print('nothing missing: all %d commands have bindings'
              % (len(registry.commands),))
        return 0

    groups = eglgen.by_extension(registry, missing)
    print('%d commands across %d extensions' % (len(missing), len(groups)))
    written = eglgen.write_missing(registry, options.package, dry_run=options.dry_run)
    for path in written:
        print('  %s %s' % ('would write' if options.dry_run else 'wrote',
                           os.path.relpath(path, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
