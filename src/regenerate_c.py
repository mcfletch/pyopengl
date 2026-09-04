#! /usr/bin/env python
"""Regenerate the C dispatch layer from the shipped PyOpenGL tree.

The C is built by ``pyopengl_accelerate``, so that is where the generated
sources land: ``accelerate/src/c/generated``.  Both packages live in this
repository and are released together, which is what makes a generator in one
and a build in the other reasonable.

Run after changing anything in ``src/cdispatch``::

    python src/regenerate_c.py                    # from the recorded registries
    python src/regenerate_c.py --update-registries  # and take newer ones
    python src/regenerate_c.py --no-fetch         # from the checkouts as they are

The Khronos registries are fetched first, so that generating is always
generating from current inputs rather than from whatever was last cloned.  See
``src/fetch_registries.py``; where there is no network the existing checkouts
are used and the run says so.

A fetch that finds a registry other than the one
``src/cdispatch/registry_lock.json`` records **stops the run**.  Every enum
value and every signature PyOpenGL ships comes out of those repositories, and
no test can catch a wrong one because the tests are generated from the same
input -- so moving to a newer registry is ``--update-registries``, a decision
with a diff attached, rather than whatever the network answered today.

The generated sources land in ``accelerate/src/c/generated`` and are compiled into the
``OpenGL_accelerate.dispatch`` extension module.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fetch_registries  # noqa: E402
from cdispatch import generate  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--package', default=os.path.join(ROOT, 'OpenGL'), help='the OpenGL package'
    )
    parser.add_argument(
        '--output',
        default=os.path.join(ROOT, 'accelerate', 'src', 'c', 'generated'),
        help='where to write',
    )
    parser.add_argument(
        '--manifest',
        default=os.path.join(
            ROOT, 'accelerate', 'src', 'c', 'generated', 'manifest.json'
        ),
        help='where to record what was generated',
    )
    parser.add_argument(
        '--no-fetch',
        action='store_true',
        help='use the registry checkouts as they are, without updating them',
    )
    parser.add_argument(
        '--update-registries',
        action='store_true',
        help=(
            'accept registries other than the ones registry_lock.json records, '
            'and record what was used'
        ),
    )
    arguments = parser.parse_args(argv)

    if not arguments.no_fetch:
        print('registries:')
        commits = fetch_registries.fetch_all()
        differences = fetch_registries.differences_from(
            commits, fetch_registries.read_lock()
        )
        if differences and not arguments.update_registries:
            print(
                '\nThe registries are not the ones the shipped bindings were '
                'generated from:',
                file=sys.stderr,
            )
            for difference in differences:
                print('  %s' % (difference,), file=sys.stderr)
            print(
                '\nEvery enum value and every signature comes out of these, and '
                'the tests are generated from the same input, so nothing here '
                'would catch a wrong one. Re-run with --update-registries to '
                'take the newer ones and record them.',
                file=sys.stderr,
            )
            return 1
        if arguments.update_registries and commits:
            fetch_registries.write_lock(commits)
            print('  recorded in %s' % (fetch_registries.LOCK,))

    report = {}
    commands, emittable, slots = generate.generate(
        arguments.package,
        arguments.output,
        report=report,
        tables_path=os.path.join(arguments.package, '_dispatch', '_tables.py'),
        stubs_root=arguments.package,
    )
    report['slots'] = len(slots)
    with open(arguments.manifest, 'w', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print(
        'bindings %d, emitted %d (%.1f%%), apis %s'
        % (
            report['total'],
            report['emitted'],
            100.0 * report['emitted'] / report['total'],
            ', '.join(report['apis']),
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
