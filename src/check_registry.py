#! /usr/bin/env python
"""Report what the shipped bindings and the Khronos registry disagree about.

Run after pulling a new registry::

    python src/check_registry.py

Exits non-zero when something needs a person: a registry command with no
binding, or a binding whose signature no longer matches.  A scheduled job can
therefore pull the registry, regenerate, run this, and open a pull request
whose body is this output.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from cdispatch import upstream  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', default=os.path.join(ROOT, 'OpenGL'))
    parser.add_argument(
        '--registry', default=os.path.join(HERE, 'khronosapi', 'xml')
    )
    parser.add_argument(
        '--verbose', action='store_true', help='list the names, not just the counts'
    )
    parser.add_argument(
        '--new-only',
        action='store_true',
        help='report only what registry_baseline.json does not already record',
    )
    parser.add_argument(
        '--write-baseline',
        action='store_true',
        help='record the current differences as the accepted baseline',
    )
    arguments = parser.parse_args(argv)

    if not os.path.isdir(arguments.registry):
        parser.error('no registry at %s' % (arguments.registry,))

    report = upstream.compare(arguments.package, arguments.registry)
    if arguments.write_baseline:
        upstream.write_baseline(report)
        print('recorded %d missing commands, %d name differences, %d enums'
              % (len(report.missing), len(report.name_mismatches),
                 len(report.missing_enums)))
        return 0

    print(report.summary())
    drift = upstream.new_drift(report)
    new = sum(len(v) for v in drift.values())
    print('\nnew since the recorded baseline:   %d' % (new,))
    for title, names in sorted(drift.items()):
        if names:
            print('  %s (%d):' % (title, len(names)))
            for name in names:
                print('     ', name)
    if arguments.new_only:
        return 1 if new else 0
    if arguments.verbose:
        for title, names in (
            ('no binding', report.missing),
            ('wrong arity', report.arity_mismatches),
            ('different argument names', report.name_mismatches),
            ('no constant', report.missing_enums),
        ):
            if names:
                print('\n%s (%d):' % (title, len(names)))
                for name in names:
                    print('   ', name)
    return 1 if new else 0


if __name__ == '__main__':
    raise SystemExit(main())
