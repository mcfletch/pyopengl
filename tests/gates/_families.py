#! /usr/bin/env python3
"""Grouping the per-API modules by the shape they have.

``OpenGL/raw/<API>/`` holds one directory per API, and the same file name
appears in several of them: ``_glgets.py`` in eight, ``_errors.py`` in nine
counting the window-system ones.  Those are the same job done for a different
API, and the way they go wrong is that one of them quietly stops doing it --
the guard that stands the error checker down when ``PYOPENGL_ERROR_CHECKING``
is off was in ``GL``'s and not in ``GLES2``'s, so ``import OpenGL.GLES2``
failed outright under a flag every other API honoured.

What is compared is the *shape*: the imports, the guard conditions, the
module-private names each branch binds, and the calls made at module level.
Two things are deliberately left out:

* **A name the module exports is its data.**  The enums, the typedefs and the
  size tables differ between APIs by definition; comparing them would make
  every module its own shape and say nothing.
* **A module path is kept as written.**  Erasing the API name there would make
  the one module importing its *own* helper look different from the six
  importing the same helper from GL.

The shape is built from identifiers rather than from ``ast.unparse``, whose
output is not promised to be identical across the six interpreters in the
matrix -- a digest of unparsed text would go red on an interpreter rather than
on a change.
"""

import ast
import hashlib
import os
import re

import paths


def _names(node):
    """The identifiers an expression mentions, sorted, each spelled once."""
    found = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.add(child.id)
        elif isinstance(child, ast.Attribute):
            found.add(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            found.add('%r' % (child.value,))
    return sorted(found)


def skeleton(tree, api):
    """A tuple summarising `tree`'s shape, with `api`'s own name erased."""
    marker = re.compile(r'\b%s\b' % re.escape(api))

    def norm(text):
        return marker.sub('API', text)

    def mentions(node):
        return '<%s>' % ','.join(norm(name) for name in _names(node))

    def statement(node, depth=0):
        pad = '  ' * depth
        if isinstance(node, ast.ImportFrom):
            return [
                '%sfrom %s import %s'
                % (
                    pad,
                    node.module or '',
                    ','.join(sorted(alias.name for alias in node.names)),
                )
            ]
        if isinstance(node, ast.Import):
            return [
                '%simport %s' % (pad, ','.join(sorted(a.name for a in node.names)))
            ]
        if isinstance(node, ast.If):
            out = ['%sif %s:' % (pad, mentions(node.test))]
            for child in node.body:
                out.extend(statement(child, depth + 1))
            if node.orelse:
                out.append('%selse:' % pad)
                for child in node.orelse:
                    out.extend(statement(child, depth + 1))
            return out
        if isinstance(node, ast.Try):
            out = ['%stry:' % pad]
            for child in node.body:
                out.extend(statement(child, depth + 1))
            for handler in node.handlers:
                out.append(
                    '%sexcept %s:'
                    % (pad, mentions(handler.type) if handler.type else '<>')
                )
                for child in handler.body:
                    out.extend(statement(child, depth + 1))
            return out
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not all(isinstance(target, ast.Name) for target in targets):
                # ``_m[0x0D33] = (1,)`` is a row of a size table rather than a
                # statement about how the module behaves.
                return []
            spelled = [norm(target.id) for target in targets]
            if not any(name.startswith('_') for name in spelled):
                return []
            return ['%s%s = ...' % (pad, ','.join(spelled))]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ['%sdef %s(%d)' % (pad, norm(node.name), len(node.args.args))]
        if isinstance(node, ast.ClassDef):
            return ['%sclass %s' % (pad, norm(node.name))]
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant):
                return []                   # a docstring is prose, not shape
            return ['%scall %s' % (pad, mentions(node.value))]
        return ['%s%s' % (pad, type(node).__name__)]

    shape = []
    for node in tree.body:
        shape.extend(statement(node))
    return tuple(shape)


def digest(shape):
    """A short, stable name for a shape, for the recorded table to carry."""
    return hashlib.sha256('\n'.join(shape).encode('utf-8')).hexdigest()[:12]


def root():
    """The directory holding one sub-directory per API."""
    return os.path.join(paths.PACKAGE, 'raw')


def apis():
    """The API directories under ``OpenGL/raw``."""
    return sorted(
        name
        for name in os.listdir(root())
        if os.path.isdir(os.path.join(root(), name)) and not name.startswith('_')
    )


def families():
    """``{filename: {api: skeleton}}`` for every name in more than one API."""
    found = {}
    for api in apis():
        directory = os.path.join(root(), api)
        for name in sorted(os.listdir(directory)):
            if not name.endswith('.py') or name == '__init__.py':
                continue
            path = os.path.join(directory, name)
            with open(path, encoding='utf-8') as handle:
                tree = ast.parse(handle.read(), filename=path)
            found.setdefault(name, {})[api] = skeleton(tree, api)
    return {name: members for name, members in found.items() if len(members) > 1}


def partition(members):
    """``[(apis, shape)]`` -- the APIs grouped by the shape they share."""
    groups = {}
    for api, shape in members.items():
        groups.setdefault(shape, []).append(api)
    return sorted((tuple(sorted(names)), shape) for shape, names in groups.items())
