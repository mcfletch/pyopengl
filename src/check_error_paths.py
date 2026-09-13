#! /usr/bin/env python3
"""Report the error paths a run of the suite never entered.

The largest single class of defect in this package's history is a handler that
does something other than what it says, and every one of them shares not having
run:

* ``_WGLQuerier.pullExtensions`` ends in ``except AttributeError: return []``,
  which is the answer for a platform that is not WGL -- and the lookup that
  raises it sat outside the ``try``, so the clause could never run and a
  ``WGL_`` specifier on a machine with no WGL raised out of whatever import
  asked.
* ``glutDestroyWindow``'s cleanup handler logged a variable the failing line
  had never assigned, so the report was a ``NameError`` raised inside the
  ``except`` -- and that second error stopped the destroy call itself, leaking
  the window and everything freeglut owned for it.
* The check-script runner passed no timeout to ``communicate()`` beside its
  ``except subprocess.TimeoutExpired``; the intent was there and the argument
  was missing, so a hung script was a cancelled job rather than a failed case.
* ``RawOpengl.render`` put a matrix mode back in a ``finally`` that could
  raise, and the buffers are swapped after that block, so the frame that had
  just been drawn went with the exception.

None of these has a syntax in common.  What they have in common is that no
case in the suite ever reached the block, so nothing could report that the
block was wrong.

This reads two things and compares them: the handlers in the package, from
their syntax trees, and the lines a run executed, from a coverage data file.
A handler no line of which ran is unentered.

The unentered set today is recorded in :data:`RECORD`, one line per handler.
A handler that is unentered and **not** recorded is a failure: it is new, and
new is the case worth stopping.

The other direction is reported and does not fail.  The record is written from
one configuration -- the `errorpaths` tox environment: numpy present,
PyOpenGL_accelerate built, and the EGL device backend on Linux -- and a great
many handlers here are for a platform or a library that configuration does not
have.  A run with more of the world in front of it legitimately enters more of
them, and that must not be a red build on somebody's laptop.  What it does
instead is say which entries have started running, so the record can be pruned
deliberately::

    python src/check_error_paths.py --write

A handler is named by where it is rather than by what line it is on::

    GLUT/special.py::cleanupWindowContext::Exception::0

so that adding a line above it does not rewrite the record.

Usage::

    coverage run -m pytest tests/
    python src/check_error_paths.py
    python src/check_error_paths.py --write     # re-record, after reading
"""

from __future__ import annotations

import argparse
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGE = os.path.join(ROOT, 'OpenGL')

#: The recorded unentered handlers, one per line: ``key  # reason``.
RECORD = os.path.join(HERE, 'error-paths-unentered.txt')

#: Directories under the package holding nothing a run would enter.
SKIP = frozenset(['__pycache__'])


def _qualname(stack):
    """The dotted name of the scope a handler sits in."""
    return '.'.join(stack) if stack else '<module>'


def _spelling(handler):
    """``'AttributeError'``, ``'OSError,TypeError'``, or ``''`` for a bare one."""
    kind = handler.type
    if kind is None:
        return ''
    items = kind.elts if isinstance(kind, ast.Tuple) else [kind]
    names = []
    for item in items:
        names.append(
            getattr(item, 'attr', None) or getattr(item, 'id', None) or '?'
        )
    return ','.join(names)


def _statement_lines(body):
    """Every line a statement in `body` starts on, however deeply nested."""
    lines = set()
    for node in body:
        for child in ast.walk(node):
            if isinstance(child, ast.stmt):
                lines.add(child.lineno)
    return lines


def handlers(tree, relative):
    """``[(key, lines, description)]`` for every error path in `tree`.

    An ``except`` clause and a ``finally`` block alike: both are code a run
    reaches only when something has gone wrong, and both have been where a
    defect sat.
    """
    found = []
    seen = {}

    def walk(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, stack + [child.name])
                continue
            if isinstance(child, ast.Try):
                scope = _qualname(stack)
                for clause in child.handlers:
                    spelling = _spelling(clause)
                    stem = '%s::%s::%s' % (relative, scope, spelling or '<bare>')
                    ordinal = seen.get(stem, 0)
                    seen[stem] = ordinal + 1
                    found.append(
                        (
                            '%s::%d' % (stem, ordinal),
                            _statement_lines(clause.body),
                            'except %s at line %d' % (spelling or '', clause.lineno),
                        )
                    )
                if child.finalbody:
                    stem = '%s::%s::<finally>' % (relative, scope)
                    ordinal = seen.get(stem, 0)
                    seen[stem] = ordinal + 1
                    found.append(
                        (
                            '%s::%d' % (stem, ordinal),
                            _statement_lines(child.finalbody),
                            'finally at line %d' % (child.finalbody[0].lineno,),
                        )
                    )
            walk(child, stack)

    walk(tree, [])
    return found


def package_handlers(root=PACKAGE):
    """Every error path in the shipped package, by key."""
    found = {}
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = sorted(n for n in subdirectories if n not in SKIP)
        for name in sorted(names):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root).replace(os.sep, '/')
            with open(path, encoding='utf-8') as handle:
                tree = ast.parse(handle.read(), filename=path)
            for key, lines, description in handlers(tree, relative):
                found[key] = (path, lines, description)
    return found


def executed(datafile=None):
    """``{absolute path: set of executed lines}`` from a coverage run."""
    from coverage import CoverageData

    data = CoverageData(basename=datafile) if datafile else CoverageData()
    data.read()
    measured = data.measured_files()
    if not measured:
        raise SystemExit(
            'the coverage data names no files, so every error path would '
            'read as unentered.  Produce it first:\n'
            '    coverage run -m pytest tests/'
        )
    return {path: set(data.lines(path) or ()) for path in measured}


def unentered(datafile=None, root=PACKAGE):
    """The keys of handlers no line of which a run executed."""
    ran = executed(datafile)
    # Coverage records absolute paths; a run from another checkout, or through
    # an install, names the same file differently.  Matched on the tail.
    by_tail = {}
    for path, lines in ran.items():
        by_tail.setdefault(os.path.normpath(path), set()).update(lines)
    found = []
    for key, (path, lines, description) in sorted(package_handlers(root).items()):
        seen = by_tail.get(os.path.normpath(path))
        if seen is None:
            found.append((key, description, 'the file is not in the coverage data'))
        elif not (lines & seen):
            found.append((key, description, 'no line of it ran'))
    return found


def recorded(path=RECORD):
    """``{key: reason}`` from the record, ignoring blanks and comments."""
    found = {}
    if not os.path.exists(path):
        return found
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, _, reason = line.partition('  # ')
            found[key.strip()] = reason.strip()
    return found


def write(entries, path=RECORD):
    """Rewrite the record from `entries`, keeping the reasons already given."""
    known = recorded(path)
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(
            '# Error paths in OpenGL/ that a run of the suite does not enter.\n'
            '# An `except` clause or a `finally` block nothing reaches is one\n'
            '# nothing has ever checked, and that is where this package keeps\n'
            '# finding handlers that raise instead of reporting.\n'
            '#\n'
            '# Written by:\n'
            '#     coverage run -m pytest tests/ && coverage combine\n'
            '#     python src/check_error_paths.py --write\n'
            '# Read by the same script without --write, which fails on a\n'
            '# handler that is unentered and NOT here.  A handler here that\n'
            '# has started running is reported and does not fail: this list\n'
            '# is written from the `errorpaths` tox environment -- numpy\n'
            '# present, PyOpenGL_accelerate built, the EGL device backend on\n'
            '# Linux -- and another configuration enters a different set.\n'
            '# Re-record from that environment, or the difference between\n'
            '# two configurations reads as a regression.\n'
            '#\n'
            '# The list is meant to shrink.  Each line is a case somebody\n'
            '# could write, or a path that has to be recorded because this\n'
            '# machine cannot reach it; where the reason is known, say it\n'
            '# after the `#` and --write will keep it.\n'
            '#\n'
            '# A handler is named by scope rather than by line, so adding a\n'
            '# line above one does not rewrite the file:\n'
            '#     <module path>::<scope>::<exceptions>::<ordinal>\n'
            '\n'
        )
        for key, _description, _why in entries:
            handle.write(
                '%s  # %s\n' % (key, known.get(key) or 'not reached by any case')
            )
    return len(entries)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--coverage', dest='datafile', default=None,
        help='the coverage data file (default: whatever .coveragerc names)',
    )
    parser.add_argument(
        '--write', action='store_true',
        help='rewrite the record from this run rather than checking against it',
    )
    arguments = parser.parse_args(argv)

    found = unentered(arguments.datafile)
    if arguments.write:
        print('recorded %d unentered error path(s) in %s'
              % (write(found), os.path.relpath(RECORD, ROOT)))
        return 0

    known = recorded()
    present = set(package_handlers())
    keys = {key for key, _description, _why in found}
    added = [item for item in found if item[0] not in known]
    # Two ways a recorded entry stops being true, and they mean different
    # things: the handler now runs, or the handler is no longer there.
    gone = sorted(key for key in known if key not in keys and key in present)
    removed = sorted(key for key in known if key not in present)

    for key, description, why in added:
        print('unentered and not recorded: %s (%s -- %s)' % (key, description, why))

    if gone:
        print(
            '\n%d recorded error path(s) ran in this configuration.  That is '
            'not a failure -- the record is written from one of them, and a '
            'machine with more of the world in front of it enters more -- but '
            'if this is that configuration, `--write` prunes them.'
            % len(gone)
        )
    if removed:
        print(
            '\n%d recorded error path(s) are no longer in the package at all. '
            '`--write` takes them out.' % len(removed)
        )

    if added:
        print(
            '\n%d error path(s) that no case reaches and nothing has said why. '
            'An error path nothing enters is one nothing has ever checked, and '
            'that is where this package keeps finding handlers that raise '
            'instead of reporting. Write a case that reaches it, or record it '
            'with the reason it cannot be reached here: %s'
            % (len(added), os.path.relpath(RECORD, ROOT)),
            file=sys.stderr,
        )
    return 1 if added else 0


if __name__ == '__main__':
    raise SystemExit(main())
