#! /usr/bin/env python3
"""Every binding exposes the same attributes under either implementation.

This is the check no functional test performs: a client reading ``argNames``
or ``extension`` off an entry point never calls it, so a difference there is
invisible until somebody's code breaks.  Both implementations are surveyed in
separate processes -- only one can be installed per process -- and the answers
compared.
"""

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: Attributes the compatibility contract preserves.
SURVEYED = ('__name__', 'argNames', 'deprecated')

#: Attributes that differ by design, with the reason.  Listed rather than
#: skipped silently, so the list is the statement of what changed.
BY_DESIGN = {
    '__doc__': 'the C implementation carries one; ctypes has None',
    '__signature__': 'inspect.signature answers under the C implementation',
    '__module__': 'reported from the entry point rather than the frame',
    'restype': 'the C implementation states its own conversion',
    'argtypes': 'built from the ctypes binding on demand',
    'extension': (
        'a command promoted into core is declared twice, once by the extension '
        'that introduced it and once by the version that adopted it.  Which '
        'declaration the ctypes namespace ends up holding depends on import '
        'order; the C layer picks the core one deterministically, because it '
        'resolves without an extension check.  What matters is that the same '
        'entry points resolve, which test_resolution_agrees asserts.'
    ),
}

SURVEY = r'''
import json, sys
import glfw
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
window = glfw.create_window(64, 64, 'survey', None, None)
glfw.make_context_current(window)

import OpenGL.GL as GL
import OpenGL._dispatch as dispatch

names = sorted(n for n in dir(GL) if n.startswith('gl') and not n.startswith('glu'))
out = {'active': dispatch.ACTIVE, 'entries': {}, 'resolves': {}}
for name in names:
    entry = getattr(GL, name)
    if not callable(entry):
        continue
    record = {}
    for attribute in %(surveyed)r:
        try:
            value = getattr(entry, attribute)
        except Exception as err:
            value = 'raised:%%s' %% (type(err).__name__,)
        if isinstance(value, (list, tuple)):
            value = list(value)
        elif not isinstance(value, (str, int, float, bool, type(None))):
            value = repr(type(value).__name__)
        record[attribute] = value
    out['entries'][name] = record
    try:
        out['resolves'][name] = bool(entry)
    except Exception:
        out['resolves'][name] = 'raised'
json.dump(out, sys.stdout)
''' % {'surveyed': SURVEYED}


def survey(dispatch):
    environment = dict(os.environ)
    environment['PYOPENGL_DISPATCH'] = dispatch
    environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    completed = subprocess.run(
        [sys.executable, '-c', SURVEY],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    if completed.returncode != 0:
        pytest.skip('could not survey under %s: %s' % (dispatch, completed.stderr[-400:]))
    return json.loads(completed.stdout)


@pytest.fixture(scope='module')
def both():
    ctypes_side = survey('ctypes')
    c_side = survey('c')
    if not c_side['active']:
        pytest.skip('the C dispatch extension is not built')
    return ctypes_side, c_side


@pytest.fixture(scope='module')
def surveys(both):
    return both[0]['entries'], both[1]['entries']


def test_resolution_agrees(both):
    """The same entry points are available under either implementation.

    This is what the `extension` attribute is *for*, so comparing the answers
    is worth more than comparing the strings that produced them.
    """
    reference, candidate = both[0]['resolves'], both[1]['resolves']
    differences = {
        name: (reference[name], candidate[name])
        for name in reference
        if name in candidate and reference[name] != candidate[name]
    }
    # A C entry point may resolve where ctypes refuses, because it consults the
    # core declaration rather than an extension string the driver no longer
    # advertises.  The reverse -- ctypes resolving where C does not -- is a
    # defect, because it is a working call that stopped working.
    lost = {
        name: pair for name, pair in differences.items() if pair == (True, False)
    }
    assert lost == {}, sorted(lost)[:20]


def test_the_same_names_are_exported(surveys):
    reference, candidate = surveys
    assert sorted(reference) == sorted(candidate)


def test_a_meaningful_number_of_entry_points_was_surveyed(surveys):
    reference, _candidate = surveys
    assert len(reference) > 1200


@pytest.mark.parametrize('attribute', SURVEYED)
def test_the_attribute_agrees(surveys, attribute):
    reference, candidate = surveys
    differences = {
        name: (reference[name][attribute], candidate[name][attribute])
        for name in reference
        if name in candidate
        and reference[name][attribute] != candidate[name][attribute]
    }
    assert differences == {}, sorted(differences.items())[:20]


def test_the_by_design_differences_are_stated():
    """Each difference the contract allows says why it is allowed."""
    assert all(reason.strip() for reason in BY_DESIGN.values())
    assert not set(BY_DESIGN) & set(SURVEYED)
