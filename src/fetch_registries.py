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

**What a run used is recorded.**  Every enum value and every signature PyOpenGL
ships comes out of these two repositories, and no test can catch a wrong one
because the tests are generated from the same input.  So the commit each
registry was at is written to ``src/cdispatch/registry_lock.json``, and a
regeneration that finds something different stops rather than quietly producing
different bindings.  ``python src/regenerate_c.py --update-registries`` is how
the answer changes, which makes moving to a newer registry a decision with a
diff attached.

Vendoring the registries themselves would be the other way to get that, and it
is the wrong one: it means carrying somebody else's tree and a stale copy of it.
Recording *which* commit was used costs a hundred bytes and answers the same
question.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(HERE, 'cdispatch', 'registry_lock.json')

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


def read_lock(path=LOCK):
    """What the shipped bindings were generated from, or an empty record."""
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {'registries': {}}


def write_lock(commits, path=LOCK):
    """Record the registries a generation used."""
    urls = dict(REGISTRIES)
    recorded = {
        'comment': (
            'The Khronos registries the shipped bindings were generated from. '
            'Written by src/regenerate_c.py --update-registries; '
            'src/fetch_registries.py explains why.'
        ),
        'generated': datetime.date.today().isoformat(),
        'registries': {
            directory: {'url': urls[directory], 'commit': commit}
            for directory, commit in sorted(commits.items())
        },
    }
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(recorded, handle, indent=2, sort_keys=True)
        handle.write('\n')
    return recorded


def differences_from(commits, lock):
    """How what was just fetched differs from what the lock records.

    A registry that did not fetch is not a difference: no network is already
    reported by the fetch itself, and the run then generates from the checkout
    it has.
    """
    recorded = (lock or {}).get('registries', {})
    differences = []
    for directory, commit in sorted(commits.items()):
        known = recorded.get(directory)
        if known is None:
            differences.append(
                '%s is at %s and the lock file does not record it'
                % (directory, commit[:12])
            )
        elif known.get('commit') != commit:
            differences.append(
                '%s is at %s, the lock file records %s'
                % (directory, commit[:12], (known.get('commit') or '?')[:12])
            )
    return differences


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument(
        '--update-lock',
        action='store_true',
        help='record what was fetched as what the bindings are generated from',
    )
    options = parser.parse_args(argv)
    commits = fetch_all(quiet=options.quiet)
    if options.update_lock:
        write_lock(commits)
    return 0 if len(commits) == len(REGISTRIES) else 1


if __name__ == '__main__':
    sys.exit(main())
