"""Put the suite's own directory on ``sys.path``, for a script run directly.

A check script is launched two ways.  ``test_checks.py`` runs it as a child
with ``childenv.child_environment``, which names ``tests/`` in the child's
``PYTHONPATH`` so that ``checkutils``, ``glcontext`` and friends import by bare
name.  A person or a CI job runs the file itself -- ``python
tests/checks/check_osmesa.py`` -- and there ``sys.path`` starts at
``tests/checks``, one directory below the modules those names refer to.

Importing this first settles it either way, so a script is a program that runs
rather than one that runs under a runner::

    import suitepath  # noqa: F401  -- the suite's modules, by bare name
    import checkutils

Every other module in this tree reads the checkout's location from
``paths.ROOT`` rather than counting ``dirname`` calls.  This one cannot:
``paths`` is among the modules it makes importable.
"""

import os
import sys

#: The suite's own directory -- the parent of the one this file is in.
TESTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if TESTS not in sys.path:
    sys.path.insert(0, TESTS)
