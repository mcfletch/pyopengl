#! /usr/bin/env python3
"""GL_NV_vdpau_interop: VDPAU video surfaces as GL textures.

Every one of the ten commands is reached and called here, with the arguments
its wrapper has to convert -- the handle types, the texture-name arrays, the
``glGet``-shaped output.  What none of them can do is succeed: each acts on a
VDPAU device and its surfaces, which a unit test has no way to conjure, and the
driver answers every one of them with a well-defined GL error while there is no
device registered.

That error *is* the assertion.  A wrapper that converted an argument wrongly
would not reach the driver's check to be told so -- it would raise from the
conversion, or pass a pointer the driver reads past.  Each call is therefore
made against the code it is documented to give, and an unlisted one propagates.

The extension is advertised by Mesa as well as by NVIDIA, which is how these
came to be tested at all: on a driver that does not offer it the whole case
skips.
"""

import unittest

from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.NV.vdpau_interop import (
    GL_SURFACE_STATE_NV,
    GL_WRITE_DISCARD_NV,
    glVDPAUFiniNV,
    glVDPAUGetSurfaceivNV,
    glVDPAUInitNV,
    glVDPAUIsSurfaceNV,
    glVDPAUMapSurfacesNV,
    glVDPAURegisterOutputSurfaceNV,
    glVDPAURegisterVideoSurfaceNV,
    glVDPAUSurfaceAccessNV,
    glVDPAUUnmapSurfacesNV,
    glVDPAUUnregisterSurfaceNV,
)

#: A surface handle the driver has never issued.  Every command below is given
#: one, because with no VDPAU device there are no real ones to be had.
NO_SURFACE = 0


class TestVDPAUInterop(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def setUp(self):
        super().setUp()
        self.require_extension('GL_NV_vdpau_interop')

    # --- registering a device ---------------------------------------------
    def test_init_refuses_a_device_that_is_not_one(self):
        """Both arguments are opaque VDPAU pointers; null is not a device."""
        with self.tolerate_glerror(GL_INVALID_VALUE):
            glVDPAUInitNV(None, None)

    def test_fini_without_init_is_refused_rather_than_obeyed(self):
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glVDPAUFiniNV()

    # --- registering surfaces ---------------------------------------------
    def test_registering_a_video_surface_needs_a_device(self):
        names = np.zeros(4, 'u4')
        with self.tolerate_glerror(GL_INVALID_VALUE, GL_INVALID_OPERATION):
            glVDPAURegisterVideoSurfaceNV(None, GL_TEXTURE_2D, 4, names)

    def test_registering_an_output_surface_needs_a_device(self):
        names = np.zeros(1, 'u4')
        with self.tolerate_glerror(GL_INVALID_VALUE, GL_INVALID_OPERATION):
            glVDPAURegisterOutputSurfaceNV(None, GL_TEXTURE_2D, 1, names)

    def test_unregistering_a_surface_that_was_never_registered(self):
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            glVDPAUUnregisterSurfaceNV(NO_SURFACE)

    # --- asking about a surface -------------------------------------------
    def test_a_handle_that_is_not_a_surface_is_not_one(self):
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            assert not glVDPAUIsSurfaceNV(NO_SURFACE)

    def test_querying_a_surfaces_state(self):
        """The glGet-shaped one: a count in, a length and values out."""
        length = np.zeros(1, 'i4')
        values = np.zeros(1, 'i4')
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            glVDPAUGetSurfaceivNV(
                NO_SURFACE, GL_SURFACE_STATE_NV, 1, length, values)

    # --- mapping ----------------------------------------------------------
    def test_declaring_how_a_surface_will_be_accessed(self):
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            glVDPAUSurfaceAccessNV(NO_SURFACE, GL_WRITE_DISCARD_NV)

    def test_mapping_surfaces_takes_an_array_of_handles(self):
        surfaces = np.zeros(2, 'uintp')
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            glVDPAUMapSurfacesNV(2, surfaces)

    def test_unmapping_surfaces_takes_the_same_array(self):
        surfaces = np.zeros(2, 'uintp')
        with self.tolerate_glerror(GL_INVALID_OPERATION, GL_INVALID_VALUE):
            glVDPAUUnmapSurfacesNV(2, surfaces)


if __name__ == '__main__':
    unittest.main()
