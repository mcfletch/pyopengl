#! /usr/bin/env python3
"""GLU and GLE ship stubs, the way GLUT and every registry API do.

The three hand-maintained libraries -- GLU, GLUT, GLE -- are not in the Khronos
registry, so the registry-driven emitter has nothing to say about them.  Without
a stub beside it, ``from OpenGL.GLU import *`` puts no name a checker can see
into the caller's namespace, and every program that draws a sphere or projects
a point is unchecked from its import line.

The cases that matter are the last two.  A stub carrying the C form where the
Python form takes fewer arguments makes the documented call an error -- that is
what cost PyOpenGL 4.0.0a4 a re-release over ``glDeleteTextures`` -- and GLU
and GLE are full of such wrappers: ``gleExtrusion`` takes five arguments where
the C entry point takes seven, because the two counts are read off the arrays.
So the runtime form is what the stub is held against, and the runtime form is
computed by the wrapper machinery rather than by anything the generator wrote.
"""

import ast
import inspect
import os

import paths
import pytest

PACKAGE = os.path.join(paths.ROOT, 'OpenGL')

#: The hand-maintained APIs, and one entry point apiece that a program cannot
#: do without -- so a stub that regressed to empty fails loudly.
APIS = ['GLU', 'GLE', 'GLUT']


def stub_for(api):
    return os.path.join(PACKAGE, api, '__init__.pyi')


def declared(api):
    """{name: node} for everything an API's stub declares at module level."""
    path = stub_for(api)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # A later declaration wins, as it does in the namespace itself.
            found[node.name] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node
    return found


def python_arguments(entry_point):
    """The names the Python form takes, or None where nothing records them.

    Three shapes reach here.  A ``wrapper.Wrapper`` computes ``pyConverterNames``
    as it is built, dropping whatever ``setPyConverter`` took out -- the counts
    GLE reads off its arrays.  A plain function carries its own signature.  A
    bare entry point carries the C argument names.
    """
    names = getattr(entry_point, 'pyConverterNames', None)
    if names is not None:
        return list(names)
    if getattr(entry_point, 'wrappedOperation', None) is not None:
        # A lazy wrapper: its own parameter list is what a caller passes, and
        # `wrappedOperation.argNames` is the C form it was built over.  Neither
        # is recorded in a form this can read, so the stub is not held to it
        # here; `test_lazy_wrapper_stubs.py` covers that mechanism.
        return None
    declared_names = getattr(entry_point, 'argNames', None)
    if declared_names is not None:
        return list(declared_names)
    try:
        signature = inspect.signature(entry_point)
    except (TypeError, ValueError):                 # pragma: no cover
        return None
    parameters = list(signature.parameters.values())
    if any(parameter.kind is parameter.VAR_POSITIONAL for parameter in parameters):
        return None                                 # takes anything
    return [parameter.name for parameter in parameters]


def stub_minimum(node):
    """The fewest positional arguments the stub will accept."""
    arguments = node.args
    if arguments.vararg is not None:
        return 0
    positional = arguments.posonlyargs + arguments.args
    return len(positional) - len(arguments.defaults)


#: What an entry point of each library is called.  Selecting by name rather
#: than by what a value looks like: an entry point is a ctypes function
#: pointer, a Wrapper, or a plain function depending on how it is wrapped, and
#: those are not distinguishable from the machinery that shares the namespace.
PREFIXES = {
    'GLU': ('glu',),
    'GLE': ('gle', 'rot_', 'urot_', 'uview'),
    'GLUT': ('glut', 'fg'),
}


def entry_points(api):
    """(name, entry point) for every callable the package offers."""
    module = pytest.importorskip('OpenGL.%s' % (api,))
    found = []
    for name in sorted(dir(module)):
        if name.startswith('_') or not name.startswith(PREFIXES[api]):
            continue
        value = getattr(module, name)
        if not callable(value) or isinstance(value, type):
            continue
        found.append((name, value))
    return found


@pytest.mark.parametrize('api', APIS)
def test_the_stub_exists(api):
    assert os.path.exists(stub_for(api)), (
        'OpenGL/%s/__init__.pyi is missing, so every program using %s is '
        'unchecked from its import line.' % (api, api)
    )


@pytest.mark.parametrize('api', APIS)
def test_an_unknown_name_does_not_error(api):
    """Each namespace carries implementation leakage a caller may still touch."""
    path = stub_for(api)
    with open(path, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=path)
    assert any(isinstance(node, ast.FunctionDef) and node.name == '__getattr__'
               for node in tree.body), (
        'without a module __getattr__ the stub makes every name it does not '
        'list an error, which is worse than having no stub.'
    )


@pytest.mark.parametrize('api', APIS)
def test_it_covers_the_namespace_the_package_offers(api):
    module = pytest.importorskip('OpenGL.%s' % (api,))
    prefix = {'GLU': ('glu', 'GLU_'), 'GLE': ('gle', 'GLE_'),
              'GLUT': ('glut', 'GLUT_')}[api]
    offered = {name for name in dir(module)
               if name.startswith(prefix) and not name.startswith('_')
               and not inspect.ismodule(getattr(module, name))}
    missing = sorted(offered - set(declared(api)))
    assert not missing, (
        '%d name(s) OpenGL.%s offers are not in its stub: %s'
        % (len(missing), api, ', '.join(missing[:20]))
    )


def arity_cases():
    """Every entry point whose Python form is known, across the three APIs."""
    cases = []
    for api in APIS:
        for name, entry_point in entry_points(api):
            names = python_arguments(entry_point)
            if names is not None:
                cases.append((api, name, len(names)))
    return cases


ARITY = arity_cases()


def test_there_are_entry_points_to_check():
    """A collection that found nothing would make every case below vacuous."""
    assert len(ARITY) > 80


UNNAMED = [(api, name, entry_point) for api in APIS
           for name, entry_point in entry_points(api)
           if getattr(entry_point, 'argtypes', None)
           and not getattr(entry_point, 'argNames', None)]


@pytest.mark.parametrize('api,name,entry_point', UNNAMED,
                         ids=['%s.%s' % (a, n) for a, n, _e in UNNAMED])
def test_an_entry_point_names_the_arguments_it_takes(api, name, entry_point):
    """A declaration that gives argument types but no names is short a name.

    PyOpenGL reports a failed call by naming the argument that failed, and a
    wrapper finds an argument to convert by looking its name up, so an unnamed
    one is reachable only by position and unmentionable in the error.  It also
    leaves a stub with nothing to call the parameter.
    """
    raise AssertionError(
        '%s takes %d argument(s) and names none of them.'
        % (name, len(entry_point.argtypes))
    )


@pytest.mark.parametrize('api,name,takes', ARITY,
                         ids=['%s.%s' % (a, n) for a, n, _t in ARITY])
def test_a_stub_does_not_demand_more_than_the_entry_point_takes(api, name, takes):
    node = declared(api).get(name)
    if not isinstance(node, ast.FunctionDef):
        pytest.skip('%s is not declared as a function in the %s stub' % (name, api))
    fewest = stub_minimum(node)
    assert fewest <= takes, (
        '%s takes %d argument(s); the %s stub demands %d, so the call the '
        'library documents is an error to a checker.'
        % (name, takes, api, fewest)
    )
