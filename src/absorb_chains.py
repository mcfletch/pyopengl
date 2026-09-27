#! /usr/bin/env python
"""Hand a friendly module's customisation chain over to the annotation table.

A generated friendly module states what makes its Python signature differ from
the C one as a chain of calls::

    glUniform4fv = wrapper.wrapper(glUniform4fv).setInputArraySize('value', None)

Every one of those is in ``src/cdispatch/annotations.json``, because the table
was extracted from these very chains, and ``define()`` applies the table to
every command it defines.  So a chain is a second copy, and applying it on top
of the table's is an error.  This finds any module still carrying one and drops
it, leaving the module's hand-written code where it is.  A chain using a call
the table does not express, or an output size it cannot state, stays.  A module
whose remaining code wraps a command the table also customises is reported,
since that code applies the conversion a second time::

    python src/absorb_chains.py            # say what would change
    python src/absorb_chains.py --write
"""

import argparse
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: The calls the annotation table expresses.  ``customise_entry`` rebuilds
#: ``setOutput`` as well now, and ``_statable`` below refuses the image sizes it
#: cannot state -- but absorbing them waits on the question
#: ``src/check_absorption.py`` raised: rewriting a module applies the rebuild
#: rule to *every* command in it, including ones whose chain said nothing, and
#: on 123 of 2,273 that adds an array conversion the file did not have.
ABSORBABLE = frozenset(['setInputArraySize', 'setInputArrayCount', 'setOutput'])

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


def _customised(name):
    """Whether ``define()`` replaces this command.

    ``customise_entry`` wraps a command when the table gives one of its
    parameters an array conversion or an output, and leaves it alone when an
    output has a size the rule cannot state.
    """
    from OpenGL import _declarations

    parameters = _declarations.annotations().get(name, {}).get('parameters', {})
    if not any(bits.get('array') or bits.get('out') for bits in parameters.values()):
        return False
    return _declarations._output_parameters(parameters) is not None


def _table_setters_applied(node):
    """The names ``node`` wraps with a call the table also makes.

    ``wrapper.wrapper(name).setInputArraySize(...)`` inside a function, or one
    the table cannot state and so was not dropped: on a command ``define()``
    has customised, that applies the conversion a second time.  A wrapper that
    only adds ``setPyConverter`` or ``setReturnValues`` over the customised
    entry point is layering on it, not repeating it.
    """
    names = set()
    for inner in ast.walk(node):
        if not (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in ABSORBABLE
        ):
            continue
        base = inner.func.value
        while (
            isinstance(base, ast.Call)
            and isinstance(base.func, ast.Attribute)
            and base.func.attr != 'wrapper'
        ):
            base = base.func.value
        if (
            isinstance(base, ast.Call)
            and base.args
            and isinstance(base.args[0], ast.Name)
        ):
            names.add(base.args[0].id)
    return names


def classify(text, api='GL'):
    """``('absorbable', lines)``, or a reason the module is left alone.

    The absorbable chains are dropped and everything else in the module is
    kept, hand-written code included: ``define()`` has put the customised entry
    point in the namespace before that code runs, so a ``@lazy`` override or an
    alias takes the customised one.  What cannot be kept is code that applies
    one of the table's own calls to a command the table customises, because
    the conversion would then be applied twice.
    """
    if '_define(globals()' not in text:
        return 'not a generated friendly module', ()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 'will not parse', ()

    chain_lines, kept = [], []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            dumped = ast.dump(node)
            if '_define' in dumped or '_EXTENSION_NAME' in dumped:
                continue
            setters = {
                name for name in _chain_calls(node.value) if name.startswith('set')
            }
            command = getattr(node.targets[0], 'id', None)
            if (
                setters
                and setters <= ABSORBABLE
                and command
                and _statable('%s.%s' % (api, command), setters)
            ):
                chain_lines.append((node.lineno, node.end_lineno))
                continue
        kept.append(node)

    for node in kept:
        for name in _table_setters_applied(node):
            if _customised('%s.%s' % (api, name)):
                return 'repeats a customisation the table makes', ()
    if not chain_lines:
        return 'nothing to absorb', ()
    return 'absorbable', tuple(chain_lines)


def rewrite(text, chain_lines):
    """Drop the chain statements; define() applies the table."""
    lines = text.splitlines(keepends=True)
    drop = set()
    for start, end in chain_lines:
        drop.update(range(start - 1, end))
    return ''.join(line for index, line in enumerate(lines) if index not in drop)


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
                with open(path + '.partial', 'w', encoding='utf-8') as handle:
                    handle.write(rewrite(text, chain_lines))
                os.replace(path + '.partial', path)

    for verdict, count in sorted(counts.items(), key=lambda item: -item[1]):
        print('  %-32s %5d' % (verdict, count))
    print('%s %d modules' % ('rewrote' if options.write else 'would rewrite', len(changed)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
