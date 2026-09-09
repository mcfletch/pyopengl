#! /usr/bin/env python3
"""The API stub describes the wrappers ``OpenGL.GL`` actually exports.

``OpenGL/GL/__init__.py`` ends with ``from OpenGL.GL.exceptional import *``, so
for every name in that module's ``__all__`` the callable a program reaches is
the hand-written wrapper rather than the generated entry point.  Several of
those wrappers exist in order to accept a shorter call than the C one:
``glDeleteTextures(textures)`` reads the count from the array it is handed, and
each wrapper's docstring gives the form it takes.

``OpenGL/GL/__init__.pyi`` is generated from the registry, which describes the C
entry point.  Where the wrapper takes fewer arguments than the C form, a stub
carrying the C form reports an error against a call the wrapper documents and
implements -- so a checker contradicts the library.  These hold the stub to the
wrapper it stands for.
"""

import ast
import inspect
import os

import paths
import pytest

from cdispatch import exceptional as exceptional_registry

from OpenGL.GL import exceptional

#: The stub a program's ``from OpenGL.GL import ...`` is checked against.
API_STUB = os.path.join(paths.ROOT, 'OpenGL', 'GL', '__init__.pyi')


#: Where the wrappers are written.
SOURCE = os.path.join(paths.ROOT, 'OpenGL', 'GL', 'exceptional.py')


def _wrapper_definitions():
    """Every ``def`` in ``exceptional.py``, by name.

    Not only the top-level ones: ``glBegin`` and ``glEnd`` are defined inside
    the branch that error checking selects, and are wrappers there just the
    same.
    """
    with open(SOURCE, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=SOURCE)
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }


def _is_lazy(definition):
    """Whether ``OpenGL.lazywrapper.lazy`` decorates this one.

    ``lazy`` passes the entry point in as the first argument and binds it, so
    the wrapper's first parameter is not one a caller supplies.
    """
    for decorator in definition.decorator_list:
        function = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(function, ast.Name) and function.id == '_lazy':
            return True
    return False


def _wrapper_parameters(name):
    """The wrapper's own parameter list: (required, most, takes_var_args).

    Read from the source rather than from the callable.  ``lazy`` returns a
    ``Curry``, and the accelerated ``Curry`` is a Cython class: it reports no
    signature, and does not carry the ``wrapperFunction`` attribute the
    Python one documents.  Introspecting the exported object would therefore
    answer differently depending on whether PyOpenGL-accelerate is installed,
    while the parameter list itself is the same either way.
    """
    definition = _wrapper_definitions().get(name)
    if definition is None:
        # Built by a factory -- glMap1d and its kin -- so the closure is what
        # a caller reaches and it introspects cleanly.
        signature = inspect.signature(getattr(exceptional, name))
        fixed = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
        ]
        variadic = len(fixed) != len(signature.parameters)
        defaulted = sum(1 for p in fixed if p.default is not p.empty)
        return len(fixed) - defaulted, len(fixed), variadic
    arguments = definition.args
    positional = arguments.posonlyargs + arguments.args
    required = len(positional) - len(arguments.defaults)
    most = len(positional)
    if _is_lazy(definition):
        # The bound entry point is not an argument a caller supplies.
        required -= 1
        most -= 1
    return required, most, arguments.vararg is not None


def _stub_definitions():
    """Every ``def`` at the top level of the API stub, by name.

    A name may have several: an overload set is how a stub says a wrapper takes
    more than one shape of call.
    """
    with open(API_STUB, encoding='utf-8') as handle:
        tree = ast.parse(handle.read(), filename=API_STUB)
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    return definitions


def _stub_required_arguments(definition):
    """How many positional arguments this ``def`` line demands."""
    arguments = definition.args
    positional = arguments.posonlyargs + arguments.args
    return len(positional) - len(arguments.defaults)


#: The exceptional names the API stub describes.  The dispatchers that take
#: only ``*args`` -- glColor, glVertex and their kin -- have no stub and fall to
#: the module's ``__getattr__``, which types them as ``Any``: untyped, but not
#: contradicted, so there is nothing here to hold them to.
STUBBED = sorted(name for name in exceptional.__all__ if name in _stub_definitions())


def test_the_stub_describes_every_wrapper_it_can():
    """The names worth checking are present, so a rename does not empty this."""
    assert 'glDeleteTextures' in STUBBED
    assert len(STUBBED) >= 7


@pytest.mark.parametrize('name', STUBBED)
def test_a_stub_does_not_demand_more_than_the_wrapper_needs(name):
    """A documented call must not be an error to a checker.

    The stub may offer more shapes than the wrapper needs -- ``glDeleteTextures``
    takes the C pair as well -- but the shortest call it admits cannot be longer
    than the shortest the wrapper accepts, or the checker rejects the call the
    docstring gives.
    """
    required, _, variadic = _wrapper_parameters(name)
    if variadic and not required:
        pytest.skip(
            'the wrapper takes only *args, which sets no lower bound; '
            'the form it documents is checked against the registry instead'
        )
    offered = min(
        _stub_required_arguments(definition)
        for definition in _stub_definitions()[name]
    )
    assert offered <= required, (
        '%s: the wrapper takes %d argument(s), the stub demands %d'
        % (name, required, offered)
    )


@pytest.mark.parametrize('entry', exceptional_registry.ENTRIES, ids=lambda e: e.name)
def test_the_registry_claims_a_call_the_wrapper_can_take(entry):
    """The Pythonic form the generator emits is one the wrapper accepts.

    Without this the stub and the registry would agree with each other and
    both be wrong: the emitter writes what the row says, and the row is where
    a mistake about the wrapper would sit.  This is the only check that reads
    the wrapper itself, so it is what keeps the row honest.
    """
    wanted = len(entry.parameters)
    required, most, variadic = _wrapper_parameters(entry.name)
    assert required <= wanted, (
        '%s: the registry offers %d argument(s), the wrapper requires %d'
        % (entry.name, wanted, required)
    )
    assert variadic or wanted <= most, (
        '%s: the registry offers %d argument(s), the wrapper takes at most %d'
        % (entry.name, wanted, most)
    )


@pytest.mark.parametrize('entry', exceptional_registry.ENTRIES, ids=lambda e: e.name)
def test_the_c_form_is_offered_only_where_the_wrapper_passes_it_through(entry):
    """A stub must not describe a call that raises ``TypeError``.

    ``glDeleteTextures`` hands a ``(size, array)`` pair to the entry point
    unchanged, so both calls are real.  The ``glMap`` family computes the
    strides and takes the short call alone, so the C form is not a call that
    exists and the stub replaces it rather than adding to it.
    """
    definitions = _stub_definitions()[entry.name]
    assert len(definitions) == (2 if entry.keeps_c_form else 1), (
        '%s: %d stub definition(s) for keeps_c_form=%r'
        % (entry.name, len(definitions), entry.keeps_c_form)
    )
