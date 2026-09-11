"""A module that cannot work here reports it as an ImportError.

Some modules need a library that exists on one platform and not the next:
:mod:`OpenGL.EGL.gbmdevice` loads ``libgbm``, which is Linux graphics
infrastructure and is absent on Windows and macOS.  Needing it is fine.
Letting the loader's ``OSError`` out of the import is not: ImportError is the
language's word for "this module is not usable here", and it is what every
``try: import ... except ImportError`` around the module is written to catch.
An OSError instead walks straight past all of them.

Which modules these are, and which libraries each may name, is
:data:`backends.OPTIONAL_MODULES`, which the module walk reads too.
"""

import importlib

import pytest
from backends import OPTIONAL_MODULES


@pytest.mark.parametrize('name', sorted(OPTIONAL_MODULES))
def test_it_imports_or_says_why_not(name):
    try:
        importlib.import_module(name)
    except ImportError:
        pass  # the supported answer for "not available here"


@pytest.mark.parametrize('name', sorted(OPTIONAL_MODULES))
def test_the_reason_names_the_library(name):
    """A bare ImportError leaves the reader guessing which library is missing.

    Any library the module lists satisfies that.  On a platform with no EGL at
    all -- macOS -- the EGL binding refuses before gbm is ever reached, and it
    names EGL, which is the library the reader has to find first.
    """
    try:
        importlib.import_module(name)
    except ImportError as raised:
        assert any(library in str(raised)
                   for library in OPTIONAL_MODULES[name]), str(raised)
