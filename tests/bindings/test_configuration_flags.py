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
