#! /usr/bin/env python3
"""Every wrapper the friendly modules put over an entry point is stubbed as it.

``OpenGL.lazywrapper.lazy`` is how a friendly module replaces a generated entry
point with one that takes a shorter call: ``glBufferData(target, data)`` reads
the size from the array, ``glDeleteFramebuffers(framebuffers)`` reads the count
from its argument.  The module rebinds the name, so that wrapper is what a
program reaches.

The stubs come from the registry, which describes the C entry point.  Where the
wrapper takes fewer arguments, a stub carrying the C form makes the documented
call an error to a type checker -- which is what a user's checker reads, and
what cost PyOpenGL 4.0.0a4 a re-release over ``glDeleteTextures``.

That one was in ``OpenGL/GL/exceptional.py`` and is covered by
``test_exceptional_stubs.py``.  This is the same fault in the other mechanism:
``@_lazy`` in a friendly module, of which there are far more.
"""

import ast
import os
import re

import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')
#: A wrapper is held against the stub for *its own* namespace: a name may be
#: wrapped in GLES3 and not in GL, and comparing across the two asks the wrong
#: question.
def _api_stub(api):
    return os.path.join(PACKAGE, api, '__init__.pyi')


def _required_of(definition):
    """Positional arguments a caller must supply to this wrapper.

    ``lazy`` binds the entry point as the first parameter, so it is not one.
    """
    arguments = definition.args
    positional = arguments.posonlyargs + arguments.args
    return len(positional) - len(arguments.defaults) - 1


def lazy_wrappers():
    """(name, required, path) for every ``@_lazy``-decorated wrapper."""
    found = []
    for directory, folders, files in os.walk(PACKAGE):
        folders[:] = [f for f in folders if f not in ('__pycache__', 'raw')]
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            try:
                with open(path, encoding='utf-8') as handle:
                    tree = ast.parse(handle.read(), filename=path)
            except (SyntaxError, UnicodeDecodeError):      # pragma: no cover
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                for decorator in node.decorator_list:
                    function = (decorator.func if isinstance(decorator, ast.Call)
                                else decorator)
                    if isinstance(function, ast.Name) and function.id in ('_lazy', 'lazy'):
                        arguments = node.args
                        variadic_only = (
                            arguments.vararg is not None
                            and len(arguments.posonlyargs + arguments.args) == 1)
                        if not variadic_only:
                            api = os.path.relpath(path, PACKAGE).split(os.sep)[0]
                            found.append((node.name, _required_of(node), api,
                                          os.path.relpath(path, paths.ROOT)))
                        break
    return found


def stub_minimums(api):
    """The fewest positional arguments each stubbed name will accept."""
    path = _api_stub(api)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    fewest = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        arguments = node.args
        positional = arguments.posonlyargs + arguments.args
        required = len(positional) - len(arguments.defaults)
        fewest[node.name] = min(fewest.get(node.name, required), required)
    return fewest


WRAPPERS = lazy_wrappers()


def test_the_walk_found_the_wrappers():
    """A walk that found nothing would make every case below vacuous."""
    assert len(WRAPPERS) > 40


@pytest.mark.parametrize('name,required,api,path', WRAPPERS,
                         ids=['%s (%s)' % (n, p) for n, _r, _a, p in WRAPPERS])
def test_a_stub_does_not_demand_more_than_the_wrapper_needs(name, required, api, path):
    fewest = stub_minimums(api)
    if name not in fewest:
        pytest.skip('%s is not in the %s stub' % (name, api))
    assert fewest[name] <= required, (
        '%s in %s takes %d argument(s); the stub demands %d, so the call the '
        'wrapper documents is an error to a checker.'
        % (name, path, required, fewest[name])
    )
