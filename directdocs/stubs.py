"""Signatures read from the ``.pyi`` stubs beside the package.

An entry point is built from the declaration tables the first time it is used,
so introspecting one gives the wrapper's shape -- often ``(*args)`` -- rather
than the call's, and its ``__annotations__`` are populated only where
``OpenGL.TYPE_ANNOTATIONS`` is set.  The stubs carry the types either way: one
per module, generated from the same tables in the same pass as the C dispatch,
which is what makes them the source the documentation reads.

The signature a stub gives is used where there is one and the introspected one
where there is not, so a module nothing generated a stub for -- ``OpenGL.Tk``
and its neighbours -- is documented exactly as it was.
"""

from __future__ import annotations

import ast
import functools
import os
import sys
from typing import Optional

__all__ = ('stub_path', 'read_stub', 'signatures')

#: The packages whose stubs are read.  A dotted name outside these is not ours
#: to find a stub for: ``os.path`` has one in typeshed, which is not a file
#: beside the module and not what this documents.
ROOT_PACKAGES = ('OpenGL', 'OpenGL_accelerate')

#: What a stub calls the "and whatever else" fallback.  It is how a generated
#: stub says the module has more in it than the generator described, not an
#: entry point anybody calls.
CATCH_ALL = '__getattr__'


def stub_path(module: str) -> Optional[str]:
    """Where ``module``'s stub would be, or None if it is not one of ours.

    Built from the dotted name and the root package's directory rather than
    from the module's ``__file__``: a module built from a declaration table
    has that naming the table, and one that is not imported has none at all.
    """
    parts = module.split('.')
    if parts[0] not in ROOT_PACKAGES:
        return None
    root = sys.modules.get(parts[0])
    if root is None:
        try:
            root = __import__(parts[0])
        except ImportError:
            return None
    directory = os.path.dirname(getattr(root, '__file__', '') or '')
    if not directory:
        return None
    here = os.path.join(directory, *parts[1:])
    if os.path.isdir(here):
        return os.path.join(here, '__init__.pyi')
    return here + '.pyi'


def _argument(argument: ast.arg, default: Optional[ast.expr]) -> str:
    """``name``, ``name: type``, ``name=default`` or ``name: type = default``.

    Rendered here rather than by ``ast.unparse`` on the whole argument list,
    which spells an annotated default ``size: int | None=None``.
    """
    rendered = argument.arg
    if argument.annotation is not None:
        rendered += ': %s' % (ast.unparse(argument.annotation),)
    if default is not None:
        joiner = ' = ' if argument.annotation is not None else '='
        rendered += '%s%s' % (joiner, ast.unparse(default))
    return rendered


def _arguments(args: ast.arguments) -> str:
    """The argument list of a stubbed function, as a caller would write it."""
    positional = list(args.posonlyargs) + list(args.args)
    # Defaults align to the tail: `f(a, b=1, c=2)` has two for three arguments.
    defaults: list[Optional[ast.expr]] = [None] * (
        len(positional) - len(args.defaults)
    ) + list(args.defaults)
    parts = [
        _argument(argument, default)
        for argument, default in zip(positional, defaults)
    ]
    if args.posonlyargs:
        parts.insert(len(args.posonlyargs), '/')
    if args.vararg is not None:
        parts.append('*%s' % (_argument(args.vararg, None),))
    elif args.kwonlyargs:
        # Keyword-only arguments need something to be keyword-only after.
        parts.append('*')
    parts.extend(
        _argument(argument, default)
        for argument, default in zip(args.kwonlyargs, args.kw_defaults)
    )
    if args.kwarg is not None:
        parts.append('**%s' % (_argument(args.kwarg, None),))
    return ', '.join(parts)


def _signature(node: ast.FunctionDef, name: Optional[str] = None) -> str:
    """``name(arg: type = default) -> result`` for one stubbed function."""
    rendered = '%s(%s)' % (name or node.name, _arguments(node.args))
    if node.returns is not None:
        rendered += ' -> %s' % (ast.unparse(node.returns),)
    return rendered


def read_stub(path: str) -> dict[str, str]:
    """Every signature in the stub at ``path``, by name.

    A method is keyed ``Class.method`` and rendered under its own name, which
    is what a ``py:method`` directive inside a ``py:class`` wants.

    A stub that is absent, unreadable or unparseable answers with nothing: the
    pages are then written from introspection, which is where they came from
    before there were stubs to read.
    """
    try:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
    except OSError:
        return {}
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return {}
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == CATCH_ALL:
                continue
            found[node.name] = _signature(node)
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found['%s.%s' % (node.name, member.name)] = _signature(member)
    return found


@functools.lru_cache(maxsize=None)
def signatures(module: str) -> dict[str, str]:
    """The stubbed signatures for ``module``, by name; empty where it has none.

    Cached, because a page asks for its module's stub once per function on it.
    """
    path = stub_path(module)
    if path is None:
        return {}
    return read_stub(path)
