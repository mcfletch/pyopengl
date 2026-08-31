#! /usr/bin/env python
"""Regenerate the C dispatch layer from the shipped PyOpenGL tree.

Run after a registry update, or after changing anything in ``src/cdispatch``::

    python src/regenerate_c.py

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
    arguments = parser.parse_args(argv)

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
