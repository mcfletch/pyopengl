#! /usr/bin/env python3
"""A function derived from a C entry point carries its own customisations.

``OpenGL.GL.pointers`` builds glColorPointerd, glColorPointerf and the rest
from the one ``glColorPointer`` entry point, each chain stating the converter
for ``pointer`` and then dropping ``size``, ``type`` and ``stride``.  The C
performs the converter call, so it is swallowed; dropping an argument is not
something the C can do, so the chain demotes to a wrapper over the ctypes
binding and replays what it swallowed.  What it replays has to be its own
chain's, whatever order the chains were built in.

The record is kept on the chain: the first swallowed call answers a GLProc of
the chain's own, which carries what the chain swallowed, and the entry point
itself carries nothing.
"""

import pytest

dispatch = pytest.importorskip('OpenGL._dispatch')

from OpenGL import dispatch as _dispatch_api  # noqa: E402

if _dispatch_api.settle() != 'c':  # pragma: no cover - depends on the axis
    pytest.skip(
        'the C dispatch layer is not the implementation running: %s'
        % (_dispatch_api.status().reason,),
        allow_module_level=True,
    )

import OpenGL.GL  # noqa: E402,F401
from OpenGL import converters, wrapper  # noqa: E402
from OpenGL._dispatch import support  # noqa: E402


class Converter:
    """A pointer converter that says which chain it came from."""

    def __init__(self, label):
        self.label = label

    def __call__(self, incoming, function, arguments):
        return self.label


@pytest.fixture
def entry_point():
    """``glColorPointer``, the entry point ``OpenGL.GL.pointers`` derives from."""
    return dispatch.entry_points[('GL', 'glColorPointer')]


def converted(proc, label):
    """`proc`'s chain as far as its swallowed converter calls."""
    function = wrapper.wrapper(proc).setPyConverter('pointer', Converter(label))
    return function.setCConverter('pointer', converters.getPyArgsName('pointer'))


def dropping_arguments(function):
    """The rest of a derived chain: the calls that demote it."""
    for dropped in ('size', 'type', 'stride'):
        function = function.setPyConverter(dropped)
    return function


def derived(proc, label):
    """A one-argument setter built from `proc`, as ``pointers`` builds them."""
    return dropping_arguments(converted(proc, label))


def pointer_label(function):
    """Which chain's converter `function` applies to ``pointer``."""
    converter = function.pyConverters[function.pyConverterNames.index('pointer')]
    return getattr(converter, 'label', converter)


def test_each_derived_function_keeps_its_own_converter(entry_point):
    first = derived(entry_point, 'double')
    second = derived(entry_point, 'float')
    assert pointer_label(first) == 'double'
    assert pointer_label(second) == 'float'


def test_chains_built_side_by_side_keep_their_own_converters(entry_point):
    """Neither chain's calls land on the other, in whatever order they come."""
    first = converted(entry_point, 'double')
    second = converted(entry_point, 'float')
    second = dropping_arguments(second)
    first = dropping_arguments(first)
    assert pointer_label(first) == 'double'
    assert pointer_label(second) == 'float'


def test_a_swallowed_call_answers_a_chain_of_its_own(entry_point):
    """The chain is a GLProc for the same entry point; the entry point is untouched."""
    chain = converted(entry_point, 'double')
    assert chain is not entry_point
    assert type(chain) is type(entry_point)
    assert chain.__name__ == entry_point.__name__
    assert chain.api == entry_point.api
    assert support.swallowed_for(entry_point) == {}
    assert support.swallowed_for(chain) != {}


def test_a_chain_continues_on_the_same_object(entry_point):
    chain = converted(entry_point, 'double')
    assert chain.setStoreValues(None) is chain


def test_a_demoted_chain_replays_only_its_own_calls(entry_point):
    derived(entry_point, 'double')
    untyped = wrapper.wrapper(entry_point).setPyConverter(
        'pointer', Converter('untyped')
    )
    assert pointer_label(support.demoted_callable(untyped)) == 'untyped'


def test_the_entry_point_itself_demotes_to_the_binding(entry_point):
    """What the raw modules export carries no friendly customisation."""
    derived(entry_point, 'double')
    demoted = support.demoted_callable(entry_point)
    assert demoted is support.ctypes_callable(entry_point.__name__, entry_point.api)
