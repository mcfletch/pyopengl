"""Dispatch the test decorator to a windowing-system specific implementation.

Selection order matches ``basetestcase``:

1. Determine which backends are importable (``pygame``, ``glfw``).
2. If the ``TEST_WINDOWING`` env var is set, honour it when that backend
   is available; otherwise fall through to the first available backend.
3. Default preference when ``TEST_WINDOWING`` is unset: glfw, then pygame.
"""
from __future__ import print_function
import importlib.util

import backends


def _installed(name):
    """Check whether ``name`` is importable without actually importing it.

    Importing pygame/glfw has side effects (initialises subsystems, allocates
    memory), so we only probe for the package metadata here.
    """
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


_AVAILABLE = [name for name in backends.WINDOWED if _installed(name)]

if not _AVAILABLE:
    raise ImportError(
        'No windowing backend available for tests; install pygame or glfw'
    )

_REQUESTED = backends.requested()
if _REQUESTED is not None and backends.is_headless(_REQUESTED):
    # A headless backend has no window for the context this decorator creates:
    # egl forces PYOPENGL_PLATFORM=egl process-wide, and cgl has no window
    # server to ask.  Provide a gltest that skips rather than crashing.
    import functools
    import unittest

    _HEADLESS_REASON = (
        'windowed gltest is unavailable under the headless %s backend'
        % (_REQUESTED,)
    )

    def gltest(maybe_function=None, *args, **named):
        def wrap(function):
            @functools.wraps(function)
            def skipped(*a, **k):
                raise unittest.SkipTest(_HEADLESS_REASON)
            return skipped
        return wrap(maybe_function) if callable(maybe_function) else wrap
    _BACKEND = _REQUESTED
else:
    if _REQUESTED and _REQUESTED not in _AVAILABLE:
        raise ImportError(
            'TEST_WINDOWING=%s requested but %s is not installed'
            % (_REQUESTED, _REQUESTED)
        )
    _BACKEND = _REQUESTED or _AVAILABLE[0]

if backends.is_headless(_BACKEND):
    pass
elif _BACKEND == 'pygame':
    from testdecorator_pygame import *  # noqa: F401,F403
    from testdecorator_pygame import gltest  # noqa: F401
elif _BACKEND == 'glfw':
    from testdecorator_glfw import *  # noqa: F401,F403
    from testdecorator_glfw import gltest  # noqa: F401
else:
    raise RuntimeError('Unhandled backend: %s' % (_BACKEND,))
