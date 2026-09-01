#! /usr/bin/env python
"""Fetch the Khronos registries the generator reads.

Two repositories, because Khronos publishes them separately:

======================  ====================================================
``src/khronosapi``      KhronosGroup/OpenGL-Registry -- ``gl.xml``,
                        ``glx.xml``, ``wgl.xml``, and the extension specs
``src/eglapi``          KhronosGroup/EGL-Registry -- ``api/egl.xml``
======================  ====================================================

Both are working copies rather than vendored files, and both are ignored by
git: they are inputs, and pinning a copy of somebody else's registry in the
tree only means carrying a stale one.  ``src/regenerate_c.py`` runs this first
so that generating is always generating from current inputs.

    python src/fetch_registries.py            # clone or pull both
    python src/regenerate_c.py --no-fetch     # generate from what is here

Fetching is a shallow clone the first time and a fast-forward after.  Where
there is no network the existing checkout is used and a note is printed, so a
build without connectivity still works and still says what it did.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: Where each registry lives, and where it comes from.
REGISTRIES = (
    ('khronosapi', 'https://github.com/KhronosGroup/OpenGL-Registry.git'),
    ('eglapi', 'https://github.com/KhronosGroup/EGL-Registry.git'),
)

#: The file each one is wanted for, relative to its checkout.  Its absence
#: after a fetch is the check that the fetch did what it claimed.
WANTED = {
    'khronosapi': os.path.join('xml', 'gl.xml'),
    'eglapi': os.path.join('api', 'egl.xml'),
}


def _run(command, **named):
    return subprocess.run(
        command, capture_output=True, text=True, timeout=600, **named
    )


def fetch(directory, url, quiet=False):
    """Clone or update one registry.  Returns its commit, or None."""
    path = os.path.join(HERE, directory)
    if os.path.isdir(os.path.join(path, '.git')):
        result = _run(['git', 'fetch', '--depth', '1', 'origin'], cwd=path)
        if result.returncode == 0:
            _run(['git', 'reset', '--hard', 'FETCH_HEAD'], cwd=path)
        elif not quiet:
            print('  %s: could not fetch, using what is here' % (directory,))
    else:
        result = _run(['git', 'clone', '--depth', '1', url, path])
        if result.returncode != 0:
            if not quiet:
                print('  %s: could not clone: %s' % (directory, result.stderr.strip()))
            return None
    wanted = os.path.join(path, WANTED[directory])
    if not os.path.exists(wanted):
        if not quiet:
            print('  %s: fetched, but %s is missing' % (directory, WANTED[directory]))
        return None
    commit = _run(['git', 'rev-parse', 'HEAD'], cwd=path)
    return commit.stdout.strip() if commit.returncode == 0 else None


def fetch_all(quiet=False):
    """Every registry, as ``{directory: commit}``."""
    commits = {}
    for directory, url in REGISTRIES:
        commit = fetch(directory, url, quiet=quiet)
        if commit:
            commits[directory] = commit
            if not quiet:
                print('  %-12s %s' % (directory, commit[:12]))
    return commits


def registry_paths():
    """Where the generator should look, whether or not a fetch just ran."""
    return {
        'gl': os.path.join(HERE, 'khronosapi', 'xml'),
        'egl': os.path.join(HERE, 'eglapi', 'api'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quiet', action='store_true')
    options = parser.parse_args(argv)
    commits = fetch_all(quiet=options.quiet)
    return 0 if len(commits) == len(REGISTRIES) else 1


if __name__ == '__main__':
    sys.exit(main())
