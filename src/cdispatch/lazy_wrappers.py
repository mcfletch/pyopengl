"""The entry points a friendly module wraps with ``OpenGL.lazywrapper.lazy``.

A ``lazy`` wrapper takes the call the entry point cannot -- the count read off
the array, the buffer the call allocates -- and the decorated function's own
parameter list is the only record of what that call looks like.  So the stub
emitter reads them out of the source rather than being told: there are dozens,
they are spread across the whole package, and a hand-kept list would be one
more thing to drift.

The hand-written table in :mod:`cdispatch.exceptional` is the other half, and
stays hand-written because it carries what reading cannot see: a return type
the wrapper changes, and whether the C form still works.
"""

import ast
import os

__all__ = ['discover']


def _required_and_names(definition):
    """``(the parameters a caller must supply, all of them)``.

    ``lazy`` binds the entry point as the first parameter, so it is not one.
    """
    arguments = definition.args
    positional = (arguments.posonlyargs + arguments.args)[1:]
    optional = len(arguments.defaults)
    required = [a.arg for a in positional[:len(positional) - optional]]
    return required, [a.arg for a in positional]


def discover(package_root, api):
    """``{name: [parameter, ...]}`` for the wrappers ``OpenGL.<api>`` exports.

    Read from the source: the decorated function's own parameter list is the
    call it takes, and nothing else records it.
    """
    found = {}
    api_root = os.path.join(package_root, api)
    if not os.path.isdir(api_root):
        return found
    for directory, folders, files in os.walk(api_root):
        folders[:] = [f for f in folders if f not in ('__pycache__', 'raw')]
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            try:
                with open(os.path.join(directory, name), encoding='utf-8') as handle:
                    tree = ast.parse(handle.read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                for decorator in node.decorator_list:
                    function = (decorator.func if isinstance(decorator, ast.Call)
                                else decorator)
                    if isinstance(function, ast.Name) and function.id in ('_lazy', 'lazy'):
                        # A `*args` wrapper -- glGetActiveAttrib takes one --
                        # still has a smallest call, and that is the number
                        # the stub has to admit.
                        # Both lists: the optional parameters are part of the
                        # call too -- `glDrawBuffers(bufs)` passes one of two
                        # that both default -- so the stub carries them with
                        # defaults rather than stopping at the required ones.
                        required, names = _required_and_names(node)
                        found.setdefault(node.name, (required, names))
                        break
    return found
