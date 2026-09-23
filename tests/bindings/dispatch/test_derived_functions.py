#! /usr/bin/env python3
"""A function derived from a C entry point carries its own customisations.

``OpenGL.GL.pointers`` builds glColorPointerd, glColorPointerf and the rest
from the one ``glColorPointer`` entry point, each chain stating the converter
for ``pointer`` and then dropping ``size``, ``type`` and ``stride``.  The C
performs the converter call, so it is swallowed; dropping an argument is not
something the C can do, so the chain demotes to a wrapper over the ctypes
binding and replays what it swallowed.  What it replays has to be its own
chain's, not the first chain's to reach that entry point.
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
    """``glColorPointer``, with the process's records put back afterwards.

    The friendly modules fill the records at import, and ``demoted_callable``
    reads them for the rest of the process.
    """
    records = (support._swallowed, support._open_chains)
    saved = [dict(record) for record in records]
    try:
        yield dispatch.entry_points[('GL', 'glColorPointer')]
    finally:
        for record, before in zip(records, saved):
            record.clear()
            record.update(before)


def derived(proc, label):
    """A one-argument setter built from `proc`, as ``pointers`` builds them."""
    function = wrapper.wrapper(proc).setPyConverter('pointer', Converter(label))
    function = function.setCConverter('pointer', converters.getPyArgsName('pointer'))
    for dropped in ('size', 'type', 'stride'):
        function = function.setPyConverter(dropped)
    return function


def pointer_label(function):
    """Which chain's converter `function` applies to ``pointer``."""
    converter = function.pyConverters[function.pyConverterNames.index('pointer')]
    return getattr(converter, 'label', converter)


def test_each_derived_function_keeps_its_own_converter(entry_point):
    first = derived(entry_point, 'double')
    second = derived(entry_point, 'float')
    assert pointer_label(first) == 'double'
    assert pointer_label(second) == 'float'


def test_a_derived_chain_is_not_replayed_onto_the_entry_point(entry_point):
    derived(entry_point, 'double')
    wrapper.wrapper(entry_point).setPyConverter('pointer', Converter('untyped'))
    demoted = support.demoted_callable(entry_point)
    assert pointer_label(demoted) == 'untyped'
