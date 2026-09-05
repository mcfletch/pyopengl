"""Common code for accelerated modules"""

import logging

import OpenGL

#: The oldest accelerate whose wrapper, array-datatype and format-handler
#: accelerators track this PyOpenGL's internals.  Those do not share the
#: generated tables the dispatch extension does -- that pair is held to exact
#: equality in OpenGL._dispatch -- but they follow the same internals, so the
#: floor moves with the major version.  PyOpenGL-accelerate pins the pairing
#: from its own side; this is the backstop for an installation assembled
#: without a resolver.
needed_version = (4, 0, 0)
_log = logging.getLogger("OpenGL.acceleratesupport")
try:
    import OpenGL_accelerate

    # Read from the package, not from the _configflags snapshot: that is taken
    # when _configflags is first imported, which may be a framework's import
    # rather than the caller's, and would then predate the assignment this
    # switch exists for.
    if OpenGL.USE_ACCELERATE:
        if OpenGL_accelerate.__version_tuple__ < needed_version:
            _log.warning(
                """Incompatible version of OpenGL_accelerate found, need at least %s found %s""",
                needed_version,
                OpenGL_accelerate.__version_tuple__,
            )
            raise ImportError("""Old version of OpenGL_accelerate""")
        ACCELERATE_AVAILABLE = True
        _log.debug("""OpenGL_accelerate module loaded""")
    else:
        raise ImportError("""Acceleration disabled""")
except ImportError as err:
    _log.info("""No OpenGL_accelerate module loaded: %s""", err)
    ACCELERATE_AVAILABLE = False
