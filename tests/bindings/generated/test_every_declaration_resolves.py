#! /usr/bin/env python3
"""Every declaration in the tables names types that exist.

A generated module's declarations are held as text -- ``'_cs.GLenum'``,
``'arrays.GLfloatArray'``, ``'ctypes.c_void_p'`` -- and turned into a ctypes
binding only when something asks for one.  Where the compiled dispatch layer is
running, most never are: the entry point comes from the extension and the
declaration is registered rather than evaluated.  So a type name that resolves
to nothing sits in the table unnoticed until somebody runs on ctypes, and then
it is an ``ImportError`` on the first line of their program.

These cases evaluate the whole table, which holds the same facts either way, so
the answer does not depend on which implementation the run happens to have
selected.  ``OpenGL/raw/<API>/_errors.py`` is imported for the same reason: a
declaration reaches for it to say which checker the binding calls, and an API
without one raises only on the path that builds a binding.
"""

import importlib

import pytest

from OpenGL._declarations import (
    APIS,
    Declaration,
    api_of,
    data_declarations,
)


def _declarations():
    """Every entry point in the shipped tables, as Declarations."""
    source = data_declarations()
    found = []
    for module_name in source.module_names():
        contents = source.module_contents(module_name)
        if contents is None:                    # pragma: no cover - not generated
            continue
        api = api_of(module_name)
        for command, arguments, types in contents['commands']:
            found.append(
                Declaration(api, command, contents['extension'], module_name,
                            arguments, types)
            )
    return found


DECLARATIONS = _declarations()


def test_the_table_holds_the_declarations():
    """A table that answered nothing would make the sweep below vacuous."""
    assert len(DECLARATIONS) > 3000


def test_every_declared_type_resolves():
    """The sweep, reported as the whole list rather than the first name.

    One missing type is usually a family of them -- a GL extension declaring a
    handle nothing else uses -- and fixing them one run at a time is the slow
    way to find that out.
    """
    unresolved = []
    for declaration in DECLARATIONS:
        try:
            declaration._resolve_types()
        except Exception as error:
            unresolved.append(
                '%s.%s: %s' % (declaration.module, declaration.name, error))
    assert unresolved == [], unresolved[:20]


@pytest.mark.parametrize('api', sorted(APIS))
def test_an_api_that_is_generated_has_an_error_checker(api):
    """Every declaration in an API reads ``_errors._error_checker``."""
    errors = importlib.import_module('OpenGL.raw.%s._errors' % (api,))
    assert hasattr(errors, '_error_checker')


@pytest.mark.parametrize('api', sorted(APIS))
def test_a_binding_can_be_built_for_each_api(api):
    """Past resolving the types: the whole binding, once per API.

    Building every one of them would bind several thousand entry points to a
    driver, which is what the dispatch layer exists to avoid doing at import.
    One per API exercises the rest of the path -- the platform lookup and the
    error checker -- without that.
    """
    for declaration in DECLARATIONS:
        if declaration.api != api:
            continue
        assert declaration() is not None
        return
    pytest.fail('the tables declare no entry point for %s' % (api,))
