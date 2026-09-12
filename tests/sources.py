#! /usr/bin/env python3
"""Reading the tree's own Python, worked out once.

A question a parser can settle -- a handler that cannot fire, a foreign
function with no prototypes, two sibling modules that drifted -- is worth
asking of every file, and there are about two thousand of them here.  Parsing
them is a second or two and the answer does not change within a run, so it is
done once and cached.

``stubs`` next door does the same for the shipped ``.pyi`` surface, which is a
different question: a stub is read by a type checker and never imported.  This
is about the code that runs.

Import the names instead::

    from sources import package, suite, Module
"""

import ast
import functools
import os

import paths

#: Directories under any root that hold nothing this suite has an opinion
#: about: caches, build output, and the two Khronos repositories
#: ``src/fetch_registries.py`` clones (which are not ours and are not tracked).
SKIP = frozenset(
    [
        '__pycache__',
        '.git',
        '.tox',
        'build',
        'dist',
        'khronosapi',
        'eglapi',
    ]
)


class Module(object):
    """One parsed file, and where it came from.

    ``relative`` is how a finding names it -- ``'GL/shaders.py'`` for a
    package module, ``'gl/test_gl20.py'`` for a suite one -- so that a message
    reads the way somebody would type the path.
    """

    def __init__(self, root, relative, tree, text):
        self.root = root
        self.relative = relative
        self.tree = tree
        self.text = text

    @property
    def path(self):
        """The absolute path, for a message that has to be opened."""
        return os.path.join(self.root, self.relative)

    def where(self, node):
        """``'GL/shaders.py:214'`` for a node in this module."""
        return '%s:%s' % (self.relative, getattr(node, 'lineno', '?'))

    def __repr__(self):
        return '<Module %s>' % (self.relative,)


def _parsed(root):
    """Every ``.py`` under `root`, parsed, in path order.

    A file that will not parse is a failure of its own rather than something
    to skip past: every interpreter in the matrix has to import what ships,
    and a module nothing can read is not a module.
    """
    found = []
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = sorted(
            name for name in subdirectories if name not in SKIP
        )
        for name in sorted(names):
            if not name.endswith('.py'):
                continue
            full = os.path.join(directory, name)
            relative = os.path.relpath(full, root)
            with open(full, encoding='utf-8') as handle:
                text = handle.read()
            found.append(Module(root, relative, ast.parse(text, filename=full), text))
    return tuple(found)


@functools.lru_cache(maxsize=None)
def package():
    """Every module in the shipped package, ``OpenGL/``."""
    return _parsed(paths.PACKAGE)


@functools.lru_cache(maxsize=None)
def suite():
    """Every module in this suite, ``tests/``."""
    return _parsed(paths.TESTS)


def within(modules, *prefixes):
    """The subset whose relative path starts with any of `prefixes`."""
    return tuple(
        module
        for module in modules
        if any(module.relative.startswith(prefix) for prefix in prefixes)
    )


def calls(tree, *names):
    """Every ``Call`` node in `tree` whose callee is spelled one of `names`.

    The callee is matched on its last segment, so ``pytest.raises`` and a
    ``raises`` imported directly both answer to ``'raises'``.
    """
    wanted = frozenset(names)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Attribute):
            spelled = function.attr
        elif isinstance(function, ast.Name):
            spelled = function.id
        else:
            continue
        if spelled in wanted:
            yield node


def dotted(node):
    """``'ctypes.windll.gdi32'`` for the attribute chain at `node`, or None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


def literal(node):
    """The value of `node` where it is a string constant, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def keyword(node, name):
    """The keyword argument `name` passed at `node`, or None."""
    for item in node.keywords:
        if item.arg == name:
            return item.value
    return None
