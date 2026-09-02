#! /usr/bin/env python
"""Hand a friendly module's customisation chain over to the annotation table.

A generated friendly module states what makes its Python signature differ from
the C one as a chain of calls::

    glUniform4fv = wrapper.wrapper(glUniform4fv).setInputArraySize('value', None)

Every one of those is already in ``src/cdispatch/annotations.json``, because
the table was extracted from these very chains -- checked across the whole tree
by ``tests/cdispatch/test_annotation_wrapping.py``.  So the chain is a second
copy, and the module can stop carrying it::

    _EXTENSION_NAME = _define(globals(), 'OpenGL.raw.GL.VERSION.GL_2_0',
                              customise=True)

``customise=True`` is per module rather than global because applying a
customisation twice raises rather than doing nothing, so the tree can only be
migrated a module at a time.  When every mechanical module has been migrated
the flag becomes the default and goes.

Only modules whose chains are *entirely* absorbable are touched.  A module with
hand-written code, or one using a call the table does not express, is left
exactly as it is and reported::

    python src/absorb_chains.py            # say what would change
    python src/absorb_chains.py --write
"""

import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: The calls the annotation table expresses.  ``customise_entry`` rebuilds
#: ``setOutput`` as well now, and ``_statable`` below refuses the image sizes it
#: cannot state -- but absorbing them waits on the question
#: ``src/check_absorption.py`` raised: rewriting a module applies the rebuild
#: rule to *every* command in it, including ones whose chain said nothing, and
#: on 123 of 2,273 that adds an array conversion the file did not have.
ABSORBABLE = frozenset(['setInputArraySize'])

_DEFINE = re.compile(
    r"^(?P<head>_?E?X?T?E?N?S?I?O?N?_?N?A?M?E? ?=? ?)?"
    r"_define\(globals\(\), (?P<name>'[^']+')\)$",
    re.M,
)


def _chain_calls(node):
    """The ``.setFoo(...)`` names in a ``wrapper.wrapper(x).setFoo()`` chain."""
    names = []
    while isinstance(node, ast.Call):
        function = node.func
        if not isinstance(function, ast.Attribute):
            break
        names.append(function.attr)
        node = function.value
    return names


def _statable(name, chain_names):
    """Whether ``customise_entry`` can rebuild what this chain says.

    ``setOutput`` with an image size is the case it cannot: the size comes from
    the format and type arguments together rather than from one value.  A
    module holding one keeps its chain, because dropping it would leave a
    wrapper that looks complete and is not.
    """
    if 'setOutput' not in chain_names:
        return True
    from OpenGL import _declarations

    annotations = _declarations.annotations()
    entry = annotations.get(name)
    if entry is None:
        return False
    return _declarations._output_parameters(entry.get('parameters', {})) is not None


def classify(text, api='GL'):
    """``('absorbable', lines)``, or a reason the module is left alone."""
    if '_define(globals()' not in text:
        return 'not a generated friendly module', ()
    if 'customise=True' in text:
        return 'already migrated', ()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 'will not parse', ()

    chain_lines, calls, other = [], set(), 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr, ast.Pass)):
            continue
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith(('glInit', 'eglInit')):
                continue
            other += 1
            continue
        if isinstance(node, ast.Assign):
            dumped = ast.dump(node)
            if '_define' in dumped or '_EXTENSION_NAME' in dumped:
                continue
            names = set(_chain_calls(node.value))
            setters = {name for name in names if name.startswith('set')}
            target = node.targets[0]
            command = getattr(target, 'id', None)
            if setters and setters <= ABSORBABLE and command:
                if not _statable('%s.%s' % (api, command), setters):
                    return 'has a size the table cannot state', ()
                chain_lines.append((node.lineno, node.end_lineno))
                calls |= setters
                continue
            other += 1
            continue
        other += 1

    if other:
        return 'has hand-written code', ()
    if not chain_lines:
        return 'nothing to absorb', ()
    return 'absorbable', tuple(chain_lines)


def rewrite(text, chain_lines):
    """Drop the chain statements and ask define() to apply the table."""
    lines = text.splitlines(keepends=True)
    drop = set()
    for start, end in chain_lines:
        drop.update(range(start - 1, end))
    kept = [line for index, line in enumerate(lines) if index not in drop]
    result = ''.join(kept)
    return _DEFINE.sub(
        lambda match: '%s_define(globals(), %s, customise=True)'
        % (match.group('head') or '', match.group('name')),
        result,
    )


def _api_of(path, root):
    """``GL``, ``GLES2``, ``EGL`` -- the first directory under the package."""
    relative = os.path.relpath(path, root).split(os.sep)
    return relative[0] if len(relative) > 1 else 'GL'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--root', default=os.path.join(ROOT, 'OpenGL'))
    options = parser.parse_args(argv)

    counts, changed = {}, []
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
            verdict, chain_lines = classify(text, _api_of(path, options.root))
            counts[verdict] = counts.get(verdict, 0) + 1
            if verdict != 'absorbable':
                continue
            changed.append(path)
            if options.write:
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write(rewrite(text, chain_lines))

    for verdict, count in sorted(counts.items(), key=lambda item: -item[1]):
        print('  %-32s %5d' % (verdict, count))
    print('%s %d modules' % ('rewrote' if options.write else 'would rewrite', len(changed)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
