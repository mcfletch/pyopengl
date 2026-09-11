#! /usr/bin/env python3
"""Reading a shipped ``.pyi``, worked out once.

A stub is read by a type checker and by nothing else, so what holds one to the
package beside it is a test that reads it the same way -- and nine modules had
each written their own ``open``, ``ast.parse`` and walk over ``tree.body``, in
several shapes.  A parse is not free and the answer never changes within a run,
so it is cached: the whole-package sweep below reads about 1,300 files.

Import the names instead::

    from stubs import declarations, functions, parameter_annotation

Paths are relative to the package -- ``'GL/__init__.pyi'``,
``'GLES2/VERSION/GLES2_2_0.pyi'`` -- and resolved against :data:`paths.PACKAGE`.
"""

import ast
import functools
import os

import paths


def path(relative):
    """The file for a package-relative stub name."""
    return os.path.join(paths.PACKAGE, relative)


@functools.lru_cache(maxsize=None)
def tree(relative):
    """The parsed stub, or ``None`` where the package does not ship one.

    ``None`` rather than raising: a stub is generated, so a checkout that has
    not been generated into has none, and a case about what a stub *says*
    cannot answer that question by failing on a missing file.
    """
    full = path(relative)
    if not os.path.exists(full):
        return None
    with open(full, encoding='utf-8') as handle:
        return ast.parse(handle.read(), filename=full)


@functools.lru_cache(maxsize=None)
def declarations(relative):
    """``{name: node}`` for everything a stub declares at module level.

    Functions and annotated assignments alike, which between them are what a
    stub says a module has.  A later declaration wins, as it does in the
    namespace itself: that is how freeglut replaces a GLUT entry point and how
    ``GLU/tess.py`` replaces ``gluTessVertex``.
    """
    parsed = tree(relative)
    if parsed is None:
        return {}
    found = {}
    for node in parsed.body:
        if isinstance(node, ast.FunctionDef):
            found[node.name] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node
    return found


def functions(relative):
    """``{name: FunctionDef}`` -- the entry points a stub declares."""
    return {name: node for name, node in declarations(relative).items()
            if isinstance(node, ast.FunctionDef)}


@functools.lru_cache(maxsize=None)
def every_function(relative):
    """``[(name, FunctionDef), ...]`` in file order, duplicates kept.

    :func:`functions` answers what the *namespace* has, so a name declared
    twice appears once.  A question about the declarations themselves -- an
    ``@overload`` pair, or the C form and the Pythonic one beside it -- needs
    all of them, since a caller satisfying either is a caller a checker
    accepts.
    """
    parsed = tree(relative)
    if parsed is None:
        return ()
    return tuple((node.name, node) for node in parsed.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))


def annotations(relative):
    """``{name: annotation text}`` for the annotated assignments in a stub."""
    return {name: ast.unparse(node.annotation)
            for name, node in declarations(relative).items()
            if isinstance(node, ast.AnnAssign)}


def parameters(node):
    """The positional parameters of a declared function, in order."""
    return node.args.posonlyargs + node.args.args


def parameter_annotation(relative, entry_point, parameter):
    """What a stub says one parameter of one entry point takes, or ``None``."""
    node = functions(relative).get(entry_point)
    if node is None:
        return None
    for argument in parameters(node):
        if argument.arg == parameter:
            return ast.unparse(argument.annotation)
    return None


@functools.lru_cache(maxsize=None)
def every_stub():
    """Every shipped ``.pyi``, as package-relative names, sorted.

    What a case about the whole declared surface walks, rather than each one
    walking the package for itself.
    """
    found = []
    for directory, folders, files in os.walk(paths.PACKAGE):
        folders[:] = [name for name in folders if name != '__pycache__']
        for name in sorted(files):
            if name.endswith('.pyi'):
                found.append(os.path.relpath(
                    os.path.join(directory, name), paths.PACKAGE))
    return tuple(sorted(found))
