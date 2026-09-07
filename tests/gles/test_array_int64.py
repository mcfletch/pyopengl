#! /usr/bin/env python3
"""Verify the GL_UNSIGNED_INT64 array-type registration across array backends.

Covers the type->array maps used by the numpy and ctypes formathandlers (so the
64-bit query getters allocate/convert correctly under accelerate and pure
Python), plus a live round-trip through the timer-query getters with both a
numpy uint64 array and a ctypes c_uint64 buffer.
"""

import unittest
import ctypes

from arraycompat import object_names
from egltestcase import ESTestCase
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_UNSIGNED_INT64


class TestArrayInt64Mappings(unittest.TestCase):
    """Backend mapping registration -- no GL context required."""

    def test_arraydatatype_constant_map(self):
        from OpenGL.arrays import arraydatatype

        at = arraydatatype.GL_CONSTANT_TO_ARRAY_TYPE[GL_UNSIGNED_INT64]
        # eight bytes per element for a uint64 array
        self.assertEqual(arraydatatype.ArrayDatatype.arrayByteCount(at.zeros((4,))), 32)

    def test_ctypes_backend_maps(self):
        from OpenGL.arrays import ctypesarrays, ctypesparameters, ctypespointers

        for module in (ctypesarrays, ctypesparameters, ctypespointers):
            self.assertIn(GL_UNSIGNED_INT64, module.GL_TYPE_TO_ARRAY_MAPPING)
            self.assertEqual(
                ctypes.sizeof(module.GL_TYPE_TO_ARRAY_MAPPING[GL_UNSIGNED_INT64]), 8
            )

    def test_numpy_backend_maps(self):
        try:
            from OpenGL.arrays import numpymodule
        except ImportError:
            self.skipTest('numpy backend not available')
        import numpy

        self.assertIn(GL_UNSIGNED_INT64, numpymodule.GL_TYPE_TO_ARRAY_MAPPING)
        self.assertEqual(
            numpymodule.GL_TYPE_TO_ARRAY_MAPPING[GL_UNSIGNED_INT64], numpy.dtype('Q')
        )
        self.assertEqual(
            numpymodule.ARRAY_TO_GL_TYPE_MAPPING[numpy.dtype('Q')], GL_UNSIGNED_INT64
        )

    def test_double_wrap_modules_import(self):
        """Modules that previously raised 'Double wrapping of output parameter'."""
        import importlib

        for mod in ('OpenGL.GL.ARB.vertex_array_object', 'OpenGL.GL.EXT.histogram'):
            importlib.import_module(mod)  # must not raise


class TestArrayInt64Live(ESTestCase):
    """Live 64-bit query read-back with each array backend's buffer type."""

    api = 'gles'
    gl_version = (3, 0)

    def test_timer_query_uint64_buffers(self):
        self.require_extension('GL_EXT_disjoint_timer_query')
        try:
            import numpy as np
        except ImportError:
            self.skipTest('numpy not available')
        from OpenGL.GLES2.EXT import disjoint_timer_query as timer

        with self.allow_missing():
            ids = np.zeros(1, 'u4')
            timer.glGenQueriesEXT(1, ids)
            q = int(ids[0])
            timer.glBeginQueryEXT(timer.GL_TIME_ELAPSED_EXT, q)
            timer.glEndQueryEXT(timer.GL_TIME_ELAPSED_EXT)

            # numpy uint64 array
            nb = np.zeros(1, 'Q')
            timer.glGetQueryObjectui64vEXT(q, timer.GL_QUERY_RESULT_EXT, nb)
            # ctypes c_uint64 buffer
            cb = (ctypes.c_uint64 * 1)()
            timer.glGetQueryObjectui64vEXT(q, timer.GL_QUERY_RESULT_EXT, cb)
            self.assertEqual(int(nb[0]), int(cb[0]))
            # signed variant, ctypes
            ci = (ctypes.c_int64 * 1)()
            timer.glGetQueryObjecti64vEXT(q, timer.GL_QUERY_RESULT_EXT, ci)

            # auto-allocation: signed getter -> int64, unsigned -> uint64
            auto_i = timer.glGetQueryObjecti64vEXT(q, timer.GL_QUERY_RESULT_EXT)
            auto_u = timer.glGetQueryObjectui64vEXT(q, timer.GL_QUERY_RESULT_EXT)
            self.assertEqual(np.asarray(auto_i).dtype, np.dtype('int64'))
            self.assertEqual(np.asarray(auto_u).dtype, np.dtype('uint64'))

            timer.glDeleteQueriesEXT(1, object_names(q))
            self.check_error('timer query 64-bit')

    def test_auto_alloc_int64_getter(self):
        """glGetInteger64v auto-allocates an int64 (previously segfaulted)."""
        try:
            import numpy as np
        except ImportError:
            self.skipTest('numpy not available')
        from OpenGL.GLES3 import glGetInteger64v, GL_MAX_ELEMENT_INDEX

        value = glGetInteger64v(GL_MAX_ELEMENT_INDEX)
        self.assertEqual(np.asarray(value).dtype, np.dtype('int64'))
        self.assertGreater(int(np.asarray(value).flat[0]), 0)


if __name__ == '__main__':
    unittest.main()
