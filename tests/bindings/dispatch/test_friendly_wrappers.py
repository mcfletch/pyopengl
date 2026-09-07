"""A friendly wrapper is installed whether or not a context was current.

Some modules used to guard their hand-written wrapper with the entry point's
own truthiness -- ``if _simple.glGetCompressedTexImage:`` -- evaluated while the
module was being imported.  Whether an entry point resolves is a question about
the *current context*, and there is none at import time: glX answers anyway, so
the wrapper appeared on Linux, while wglGetProcAddress does not, so Windows was
left holding the raw entry point with its uncollapsed output argument.  The
friendly two-argument call then failed on one platform and not the other.

An entry point that really is missing raises NullFunctionError when called,
which is where the question belongs.
"""

import inspect
import re

import pytest

#: (module, name) pairs whose hand-written wrapper collapses an output
#: argument, so its signature differs from the raw entry point's.
WRAPPED = (
    ('OpenGL.GL.VERSION.GL_1_3', 'glGetCompressedTexImage'),
    ('OpenGL.GL.ARB.texture_compression', 'glGetCompressedTexImageARB'),
)


@pytest.mark.parametrize('module_name,name', WRAPPED)
def test_the_wrapper_takes_the_output_argument_optionally(module_name, name):
    """``f(target, level)`` is the documented call; ``img`` is optional."""
    import importlib

    module = importlib.import_module(module_name)
    entry_point = getattr(module, name)
    try:
        signature = inspect.signature(entry_point)
    except (TypeError, ValueError):
        pytest.fail('%s.%s is not the wrapper: %r' % (module_name, name, entry_point))
    assert list(signature.parameters) == ['target', 'level', 'img'], name
    assert signature.parameters['img'].default is None, name


@pytest.mark.parametrize('module_name,name', WRAPPED)
def test_the_wrapper_does_not_call_itself(module_name, name):
    """The wrapper delegates to the raw entry point, not to its own name."""
    import importlib

    module = importlib.import_module(module_name)
    source = inspect.getsource(getattr(module, name))
    body = source.split('\n', 1)[1]
    # The bare name, not a qualified `_simple.name` call.
    unqualified = re.search(r'(?<![.\w])%s\s*\(' % (re.escape(name),), body)
    assert unqualified is None, (
        '%s.%s calls itself; it should call the raw entry point'
        % (module_name, name)
    )
