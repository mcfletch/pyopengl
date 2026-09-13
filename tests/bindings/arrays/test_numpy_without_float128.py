#! /usr/bin/env python3
"""The numpy handler builds on a numpy that has no ``float128``.

``numpy.float128`` is the platform's 80- or 128-bit long double, and it does
not exist everywhere: numpy omits it on Windows, where MSVC's ``long double``
is a ``double``, and on some ARM builds. A handler that lists it
unconditionally therefore raises ``AttributeError: module 'numpy' has no
attribute 'float128'`` while it is being built -- so it is not one call that
fails but the whole array plug-in, and the caller sees it from whichever entry
point they happened to call first.

That is #21: the report is ``glGenTextures`` raising it, which is nothing to
do with glGenTextures.

Asked in a child with the attribute removed, because whether the handler reads
it is settled while the module is imported, and this process has already
imported it. Removing the attribute is the whole of the simulation, and on
Windows there is nothing to remove -- what the handler sees is the same either
way, which is what the cases assert.

https://github.com/mcfletch/pyopengl/issues/21
"""

import pytest

from childenv import json_from_child

pytest.importorskip('numpy', reason='the handler under test is numpy\'s')

#: Delete the attribute, then let PyOpenGL build its numpy handler and say
#: what it accepts.
#:
#: ``still_present`` is what the handler will actually see, and is the
#: precondition the cases below rest on.  A Windows numpy has none of these to
#: begin with, so ``removed`` is empty there and absence is the machine rather
#: than the simulation.
WITHOUT_FLOAT128 = '''
import json
import numpy

WIDE = ('float128', 'complex256', 'longdouble')

removed = [name for name in WIDE if hasattr(numpy, name)]
for name in removed:
    delattr(numpy, name)

report = {'removed': removed,
          'still_present': [name for name in WIDE if hasattr(numpy, name)]}
try:
    from OpenGL.arrays import numpymodule
    report['handled'] = len(numpymodule.NumpyHandler.HANDLED_TYPES)
    import OpenGL.GL                       # the import the ticket died on
    report['imported'] = True
except Exception as error:
    report['error'] = '%s: %s' % (type(error).__name__, error)
print(json.dumps(report))
'''


def test_the_handler_builds_without_it():
    answered = json_from_child(WITHOUT_FLOAT128)
    assert 'error' not in answered, answered['error']
    assert answered['imported'] is True, answered


def test_the_attributes_really_were_absent():
    """Otherwise the case above proves nothing about a numpy that lacks them.

    What matters is that the handler was built against a numpy without them,
    not how it came to be one.  Asserting the deletion instead would hold only
    where there was something to delete -- and Windows, where there is not, is
    the platform the ticket came from.
    """
    answered = json_from_child(WITHOUT_FLOAT128)
    assert answered['still_present'] == [], answered


def test_it_still_handles_the_ordinary_types():
    """A handler that dropped everything would also pass the case above."""
    answered = json_from_child(WITHOUT_FLOAT128)
    assert answered['handled'] > 5, answered
