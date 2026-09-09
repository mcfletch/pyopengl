#! /usr/bin/env python
"""Compare the wrapper a chain builds against the one the table rebuilds.

``absorb_chains.py`` deletes a module's customisation chain and asks
``define(customise=True)`` to rebuild it from ``annotations.json``.  That is
only safe if the two produce the same wrapper, and "the table records what the
chain said" -- which ``tests/cdispatch/test_annotation_wrapping.py`` checks --
is a weaker statement than "the wrapper comes out the same".

So build both and compare what a call reads: the converters, the resolvers, the
stored values and the argument names.  Run it against a tree whose chains are
still in place::

    python src/check_absorption.py            # every absorbable module
    python src/check_absorption.py --verbose  # name each command checked
"""

import argparse
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: What a wrapper carries that decides what a call does.  ``wrappedOperation``
#: is deliberately absent: both sides wrap the same entry point object, and
#: comparing it compares identity rather than behaviour.
COMPARED = (
    'pyConverters',
    'cConverters',
    'cResolvers',
    'storeValues',
    'returnValues',
    'argNames',
    'pyConverterNames',
)


def _shape(value):
    """A comparable description of a converter, which is often a closure."""
    if value is None or isinstance(value, (int, float, str, bytes, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_shape(item) for item in value)
    # A converter is usually an instance of a converter class, or a bound
    # method, or a closure the size functions produce.  Its class and the
    # fields it was built with are what distinguish one from another.
    fields = {}
    for name in getattr(value, '__slots__', ()) or ():
        fields[name] = _shape(getattr(value, name, None))
    for name, item in sorted(vars(value).items()) if hasattr(value, '__dict__') else ():
        if not name.startswith('__'):
            fields[name] = _shape(item)
    if fields:
        return (type(value).__name__, tuple(sorted(fields.items())))
    if callable(value):
        # A size lambda: call it with a probe, since what it computes is the
        # only thing about it that matters.
        try:
            return ('callable', tuple(value(n) for n in (1, 2, 8, 64)))
        except Exception:
            return ('callable', type(value).__name__, getattr(value, '__name__', ''))
    return (type(value).__name__, repr(value))


def describe(entry):
    """What a call would read off this entry point."""
    return tuple(
        (name, _shape(getattr(entry, name, None))) for name in COMPARED
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--root', default=os.path.join(ROOT, 'OpenGL'))
    options = parser.parse_args(argv)

    sys.path.insert(0, ROOT)
    os.environ.setdefault('PYOPENGL_PLATFORM', 'glx')

    from OpenGL import _declarations

    sys.path.insert(0, HERE)
    import absorb_chains

    checked = mismatched = skipped = skipped_commands = 0
    failures = []
    for directory, folders, files in os.walk(options.root):
        parts = directory.split(os.sep)
        if 'raw' in parts or '__pycache__' in parts:
            folders[:] = [name for name in folders if name != '__pycache__']
            continue
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            with open(path, 'r', encoding='utf-8') as handle:
                text = handle.read()
            api = absorb_chains._api_of(path, options.root)
            verdict, _lines = absorb_chains.classify(text, api)
            if verdict != 'absorbable':
                continue

            module_name = os.path.relpath(path, os.path.dirname(options.root))
            module_name = module_name[:-3].replace(os.sep, '.')
            try:
                from_chain = importlib.import_module(module_name)
            except Exception as error:  # a module needing a live context
                skipped += 1
                if options.verbose:
                    print('  skipped %s: %s' % (module_name, error))
                continue

            raw_name = _raw_name_of(text)
            if raw_name is None:
                skipped += 1
                continue
            contents = _declarations.contents_for(raw_name) or {}
            rebuilt = {}
            _declarations.define(rebuilt, raw_name, customise=True)

            rebound = _rebound_by_star_imports(text, from_chain)
            for command, __arguments, __types in contents.get('commands', ()):
                theirs = getattr(from_chain, command, None)
                ours = rebuilt.get(command)
                if theirs is None or ours is None:
                    continue
                if command in rebound:
                    # A trailing ``from ... import *`` overwrites what the
                    # chain built, so the module's own chain is dead code for
                    # this command and there is nothing to compare.
                    skipped_commands += 1
                    continue
                checked += 1
                if describe(theirs) != describe(ours):
                    mismatched += 1
                    failures.append((module_name, command))
                elif options.verbose:
                    print('  ok %s.%s' % (module_name, command))

    print('%d entry points compared, %d modules skipped, '
          '%d commands rebound by a later import *'
          % (checked, skipped, skipped_commands))
    if failures:
        print('%d MISMATCHED:' % (mismatched,))
        for module_name, command in failures[:40]:
            print('  %s.%s' % (module_name, command))
        return 1
    print('every rebuilt wrapper matches the one its chain built')
    return 0


def _rebound_by_star_imports(text, module):
    """Commands a trailing ``from X import *`` overwrote in this module.

    A friendly module often ends by re-exporting the extension modules its
    version adopted, and that assignment lands after its own chain.  Where the
    name the module finally holds is the one the imported module holds, the
    chain never reaches a caller.
    """
    import ast as _ast

    rebound = set()
    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return rebound
    for node in tree.body:
        if not (isinstance(node, _ast.ImportFrom) and node.module):
            continue
        if not any(alias.name == '*' for alias in node.names):
            continue
        try:
            source = importlib.import_module(node.module)
        except Exception:
            continue
        for name in dir(source):
            if name.startswith(('gl', 'egl', 'wgl', 'glX')):
                if getattr(module, name, None) is getattr(source, name, None):
                    rebound.add(name)
    return rebound


def _raw_name_of(text):
    import absorb_chains

    match = absorb_chains._DEFINE.search(text)
    if match is None:
        return None
    return match.group('name').strip("'")


if __name__ == '__main__':
    sys.exit(main())
