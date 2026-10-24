"""Tests that OpenGL_accelerate is a compatible version, disables if not"""

import logging

import OpenGL

#: The oldest OpenGL_accelerate whose wrapper, array-datatype and
#: format-handler accelerators match this PyOpenGL's internals.  These
#: accelerators do not use the generated tables, unlike the dispatch
#: extension, whose version OpenGL._dispatch requires to match exactly.  They
#: depend on the same internals, so this minimum follows the major version.
#: PyOpenGL-accelerate also pins the pairing in its own requirements.  This
#: check covers installations assembled without a dependency resolver.
needed_version = (4, 0, 0)
_log = logging.getLogger("OpenGL.acceleratesupport")
try:
    import OpenGL_accelerate

    # Read from the package instead of _configflags.  _configflags copies the
    # flags when it is first imported, which may happen in a framework's
    # import before the caller sets USE_ACCELERATE.
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
