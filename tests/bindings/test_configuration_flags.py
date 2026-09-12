#! /usr/bin/env python3
"""The flags ``OpenGL/__init__.py`` documents can be set the way it says.

A flag nobody can set is a flag nobody tests, and the two go together: until
4.0 ``SIZE_1_ARRAY_UNPACK`` was the one flag in that list which was not an
``environ_key``, so ``PYOPENGL_SIZE_1_ARRAY_UNPACK`` did nothing, no axis could
select it, and the behaviour it selects had quietly stopped working -- every
place the library read a size-1 query for itself did ``int()`` on it, which
numpy refuses for an array that is not zero-dimensional.

So this asks the small question that would have caught it: does setting the
variable reach ``_configflags``, which is what the wrappers are built from.
"""

import json

import pytest

from childenv import json_from_child

#: The flags the module docstring lists as settable, with a value that is not
#: the default -- so a flag that is not being read at all shows up as the
#: default coming back.
SETTABLE = {
    'ERROR_CHECKING': False,
    'ERROR_ON_COPY': True,
    'ARRAY_SIZE_CHECKING': False,
    'STORE_POINTERS': False,
    'SIZE_1_ARRAY_UNPACK': False,
    'USE_ACCELERATE': False,
    'CONTEXT_CHECKING': True,
    'ERROR_DEBUG_OUTPUT': False,
    'ERROR_LOGGING': True,
    'FULL_LOGGING': True,
}

REPORT = '''
import json
from OpenGL import _configflags
print(json.dumps({"value": bool(_configflags.%s)}))
'''


@pytest.mark.parametrize('name', sorted(SETTABLE))
def test_the_environment_variable_reaches_the_configuration(name):
    """``PYOPENGL_<NAME>`` is what a caller sets, and `_configflags` is what
    the wrappers are built from, so the question is whether one reaches the
    other."""
    wanted = SETTABLE[name]
    answered = json_from_child(
        REPORT % (name,), **{'PYOPENGL_%s' % (name,): '1' if wanted else '0'}
    )
    assert answered['value'] is wanted, (
        'PYOPENGL_%s=%s left _configflags.%s at %r'
        % (name, '1' if wanted else '0', name, answered['value'])
    )


def declared_defaults():
    """``NAME: default`` as ``OpenGL/__init__.py`` assigns them.

    Read from the source rather than from this process: a run started with one
    of these variables set has a different value in front of it, and the
    question is what a caller who set nothing gets.
    """
    import os
    import re

    import paths

    with open(os.path.join(paths.PACKAGE, '__init__.py'), encoding='utf-8') as handle:
        source = handle.read()
    return {
        name: value == 'True'
        for name, value in re.findall(
            r'^([A-Z][A-Z0-9_]+) = environ_key\(\s*"[A-Z0-9_]+"\s*,\s*(True|False)\s*\)$',
            source, re.M,
        )
    }


@pytest.mark.parametrize('name', sorted(SETTABLE))
def test_the_default_is_what_the_source_declares(name):
    """With nothing set, the flag is the default named in the environ_key call."""
    defaults = declared_defaults()
    assert name in defaults, (
        '%s is not declared with environ_key, so it cannot be set from the '
        'environment' % (name,)
    )
    answered = json_from_child(REPORT % (name,), **{'PYOPENGL_%s' % (name,): None})
    assert answered['value'] is defaults[name]


def test_every_documented_flag_is_covered_here():
    """A flag added to the docstring and not to SETTABLE is one nobody varies."""
    import re

    import OpenGL

    documented = set(re.findall(r'^    ([A-Z][A-Z0-9_]{3,}) --', OpenGL.__doc__, re.M))
    # These name things a caller sets in code rather than from the environment:
    # they are read while the modules are being built, before any environment
    # is consulted, or they are switches for the generator rather than the run.
    in_code_only = {
        'FORWARD_COMPATIBLE_ONLY', 'WARN_ON_FORMAT_UNAVAILABLE',
        'MODULE_ANNOTATIONS', 'TYPE_ANNOTATIONS', 'ALLOW_NUMPY_SCALARS',
        'UNSIGNED_BYTE_IMAGES_AS_STRING',
    }
    missing = documented - set(SETTABLE) - in_code_only
    assert not missing, (
        'documented flags that nothing here varies: %s' % (', '.join(sorted(missing)),)
    )


#: What the child does: build the wrappers, then set a flag, which is the
#: order that does not work.  Printed rather than raised so the case can say
#: which of the two things went wrong.
SET_TOO_LATE = '''
import json, warnings
import OpenGL.GL                     # the wrappers are built here...
import OpenGL
from OpenGL import _configflags

# The opposite of whatever is in force: setting a flag to the value it already
# has changes nothing whenever it happens, so there would be nothing to warn
# about -- and the run under PYOPENGL_ERROR_ON_COPY=1 is exactly that case.
wanted = not _configflags.ERROR_ON_COPY
with warnings.catch_warnings(record=True) as raised:
    warnings.simplefilter('always')
    OpenGL.ERROR_ON_COPY = wanted    # ...and this is already too late
print(json.dumps({
    'warned': [str(one.message) for one in raised],
    'categories': [one.category.__name__ for one in raised],
    'wanted': wanted,
    'took_effect': bool(_configflags.ERROR_ON_COPY) == wanted,
}))
'''

#: The order that does work, and must stay silent.
SET_IN_TIME = '''
import json, warnings
import OpenGL
wanted = not OpenGL.ERROR_ON_COPY
with warnings.catch_warnings(record=True) as raised:
    warnings.simplefilter('always')
    OpenGL.ERROR_ON_COPY = wanted    # before anything reads the flags
    import OpenGL.GL
from OpenGL import _configflags
print(json.dumps({
    'warned': [str(one.message) for one in raised],
    'took_effect': bool(_configflags.ERROR_ON_COPY) == wanted,
}))
'''


class TestAFlagSetAfterTheWrappersAreBuilt:
    """Assigning to a flag too late does nothing, and has to say so.

    The flags are read once, when the first entry point is built, and frozen
    into ``_configflags``; the wrappers are built from that.  So

        import OpenGL.GL
        OpenGL.ERROR_ON_COPY = True

    is an assignment that changes nothing, and until it says so the program
    runs on with the caller believing a setting is in force that is not.

    That is not a hypothetical misreading.  #5 is somebody reporting that
    ``ERROR_ON_COPY`` "doesn't trigger" after setting it exactly this way, and
    #159 is somebody else finding the same thing in a test module -- where
    pytest had imported another module, and its ``import OpenGL.GL``, before
    the one setting the flag ran.  Both spent the ticket looking at the array
    machinery, which was behaving correctly.

    https://github.com/mcfletch/pyopengl/issues/5
    https://github.com/mcfletch/pyopengl/issues/159
    """

    def test_it_warns(self):
        answered = json_from_child(SET_TOO_LATE)
        assert answered['warned'], (
            'setting ERROR_ON_COPY after the wrappers were built changed '
            'nothing and said nothing')

    def test_the_warning_names_the_flag_and_the_remedy(self):
        answered = json_from_child(SET_TOO_LATE)
        message = ' '.join(answered['warned'])
        assert 'ERROR_ON_COPY' in message, message
        assert 'PYOPENGL_ERROR_ON_COPY' in message, (
            'the message should name the environment variable, which works '
            'whatever the import order: %s' % (message,))

    def test_it_is_a_warning_rather_than_an_error(self):
        """A program doing this today keeps running; it is now told."""
        answered = json_from_child(SET_TOO_LATE)
        assert answered['categories'], answered
        assert all(name.endswith('Warning')
                   for name in answered['categories']), answered

    def test_the_assignment_still_does_not_take_effect(self):
        """The warning says so; it does not paper over it.

        Making a late assignment work would mean rebuilding every entry point
        already bound, which is not something an attribute assignment can be
        allowed to do.
        """
        answered = json_from_child(SET_TOO_LATE)
        assert answered['took_effect'] is False, answered

    def test_setting_it_in_time_is_silent_and_works(self):
        """The documented order, which must not have acquired a warning."""
        answered = json_from_child(SET_IN_TIME)
        assert answered['warned'] == [], answered
        assert answered['took_effect'] is True, answered
