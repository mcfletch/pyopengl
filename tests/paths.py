#! /usr/bin/env python3
"""Where things are, worked out once.

A test that needs the checkout -- to read the Khronos registry, to run a child
from the repository root, to find the package directory the build produced --
used to count ``os.path.dirname`` calls up from its own ``__file__``.  That
number is a fact about how deep the file happens to sit, so moving a module
into a sub-directory silently changed what ``ROOT`` meant: it still resolved,
still existed, and named the wrong directory, which surfaced as a registry
parsed as empty and a parametrised case collapsing to one ``NOTSET``.

Import the name instead::

    from paths import ROOT, SRC
"""

import os

#: This directory: the suite's own root, holding the shared framework.
TESTS = os.path.dirname(os.path.abspath(__file__))

#: The checkout: what a child process should run from, and what the paths
#: below are relative to.
ROOT = os.path.dirname(TESTS)

#: The build-time sources: the code generator, and the registry XML it reads.
SRC = os.path.join(ROOT, 'src')

#: The Khronos registry XML, present only where it has been fetched.
REGISTRY = os.path.join(SRC, 'khronosapi', 'xml')

#: The importable package under test.
PACKAGE = os.path.join(ROOT, 'OpenGL')

#: Fixtures the suites read rather than build.
DATA = os.path.join(TESTS, 'data')
