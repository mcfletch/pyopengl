#! /usr/bin/env python
"""Regenerate the C dispatch layer from the shipped PyOpenGL tree.

Run after changing anything in ``src/cdispatch``::

    python src/regenerate_c.py              # fetch the registries, then generate
    python src/regenerate_c.py --no-fetch   # generate from the checkouts as they are

The Khronos registries are fetched first, so that generating is always
generating from current inputs rather than from whatever was last cloned.  See
``src/fetch_registries.py``; where there is no network the existing checkouts
are used and the run says so.

The generated sources land in ``src/c/generated`` and are compiled into the
``OpenGL._dispatch._dispatch`` extension module.
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
        '--output', default=os.path.join(HERE, 'c', 'generated'), help='where to write'
    )
    parser.add_argument(
        '--manifest',
        default=os.path.join(HERE, 'c', 'generated', 'manifest.json'),
        help='where to record what was generated',
    )
    parser.add_argument(
        '--no-fetch',
        action='store_true',
        help='use the registry checkouts as they are, without updating them',
    )
    arguments = parser.parse_args(argv)

    if not arguments.no_fetch:
        print('registries:')
        fetch_registries.fetch_all()

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
