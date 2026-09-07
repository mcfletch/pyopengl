#! /usr/bin/env python
from __future__ import print_function
import logging, time, traceback, unittest, os, pytest

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
HERE = os.path.dirname(__file__)
import pickle

try:
    import cPickle
except ImportError as err:
    cPickle = pickle

try:
    from numpy import *
except ImportError as err:
    array = None

import OpenGL

if os.environ.get('TEST_NO_ACCELERATE'):
    OpenGL.USE_ACCELERATE = False
# OpenGL.FULL_LOGGING = True
OpenGL.FORWARD_COMPATIBLE_ONLY = False
OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True

# OpenGL.CONTEXT_CHECKING is deliberately not set here.  What an entry point
# does with no current context is decided before anything builds the entry
# points, so a module this late cannot ask the question -- and setting it
# anyway reaches calls that legitimately have no context: EGL enumerates its
# devices before there is one, and a refused enumeration reads as a machine
# with no devices on it.  tests/gl/test_no_context_calls.py settles the
# question in a subprocess instead.

# from OpenGL._bytes import bytes, _NULL_8_BYTE, unicode, as_8_bit
from OpenGL.GL import *
from OpenGL import error
from OpenGL.GLU import *
import OpenGL
from OpenGL.extensions import alternate, GLQuerier
from OpenGL.GL.framebufferobjects import *
from OpenGL.GL.EXT.multi_draw_arrays import *
from OpenGL.GL.ARB.imaging import *
from OpenGL._bytes import _NULL_8_BYTE

glMultiDrawElements = alternate(
    glMultiDrawElementsEXT,
    glMultiDrawElements,
)
import basetestcase


class TestCore(basetestcase.BaseTest):
    def test_errors(self):
        """Test for error catching/checking"""
        try:
            glClear(GL_INVALID_VALUE)
        except Exception as err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glClear"""
        try:
            glColorPointer(GL_INVALID_VALUE, GL_BYTE, 0, None)
        except Exception as err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
            assert err.baseOperation, err.baseOperation
            assert err.pyArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.pyArgs
            assert err.cArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.cArgs
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glColorPointer"""
        try:
            glBitmap(-1, -1, 0, 0, 0, 0, as_8_bit(""))
        except Exception as err:
            assert err.err in (1281, 1282), (
                """Expected invalid value (1281) or invalid operation (1282)""",
                err.err,
            )
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glBitmap"""

    if not OpenGL.ERROR_ON_COPY:

        def test_simple(self):
            """Test for simple vertex-based drawing"""
            glDisable(GL_LIGHTING)
            glBegin(GL_TRIANGLES)
            try:
                try:
                    glVertex3f(0.0, 1.0, 0.0)
                except Exception:
                    traceback.print_exc()
                glVertex3fv([-1, 0, 0])
                glVertex3dv([1, 0, 0])
                try:
                    glVertex3dv([1, 0, 4, 5])
                except ValueError:
                    # Got expected value error (good)
                    assert OpenGL.ARRAY_SIZE_CHECKING, """Should have raised ValueError when doing array size checking"""
                else:
                    assert not OpenGL.ARRAY_SIZE_CHECKING, """Should not have raised ValueError when not doing array size checking"""
            finally:
                glEnd()
            a = glGenTextures(1)
            assert a
            b = glGenTextures(2)
            assert len(b) == 2

    def test_arbwindowpos(self):
        """Test the ARB window_pos extension will load if available"""
        from OpenGL.GL.ARB.window_pos import glWindowPos2dARB

        if glWindowPos2dARB:
            glWindowPos2dARB(0.0, 3.0)

    def test_getstring(self):
        assert glGetString(GL_EXTENSIONS)

    def test_constantPickle(self):
        """Test that our constants can be pickled/unpickled properly"""
        for p in pickle, cPickle:
            v = p.loads(p.dumps(GL_VERTEX_ARRAY))
            assert v == GL_VERTEX_ARRAY, (v, GL_VERTEX_ARRAY)
            assert v.name == GL_VERTEX_ARRAY.name, v.name

    def test_nonFloatColor(self):
        """Test that we handle non-floating-point colour inputs"""
        for notFloat, shouldWork in ((0, True), (object(), False), (object, False)):
            try:
                glColor4f(0, 1, 1, notFloat)
            except Exception:
                if shouldWork:
                    raise
            else:
                if not shouldWork:
                    raise RuntimeError(
                        """Expected failure for non-float value %s, succeeded"""
                        % (notFloat,)
                    )

    if array:

        def test_arrayTranspose(self):
            m = glGetFloatv(GL_MODELVIEW_MATRIX)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            t = eye(4)
            t[3, 0] = 20.0

            # the following glMultMatrixf call ignored this transpose
            t = t.T
            if OpenGL.ERROR_ON_COPY:
                t = ascontiguousarray(t)

            glMultMatrixd(t)

            m = glGetFloatv(GL_MODELVIEW_MATRIX)
            assert allclose(m[-1], [0, 0, 0, 1]), m

    if array:
        # currently crashes in py_buffer operation, so reverted to raw numpy
        # api
        def test_mmap_data(self):
            """Test that we can use mmap data array

            If we had a reasonable lib that dumped raw image data to a shared-mem file
            we might be able to use this for movie display :)
            """
            fh = open('mmap-test-data.dat', 'wb+')
            fh.write(_NULL_8_BYTE * (32 * 32 * 3 + 1))
            fh.flush()
            fh.close()
            # using memmap here...
            data = memmap('mmap-test-data.dat')
            for i in range(0, 255, 2):
                glDrawPixels(
                    32,
                    32,
                    GL_RGB,
                    GL_UNSIGNED_BYTE,
                    data,
                )
                self.flip()
                data[::2] = i
                time.sleep(0.001)

    if array:

        def test_vbo(self):
            """Test utility vbo wrapper"""
            from OpenGL.arrays import vbo

            if not vbo.get_implementation():
                return
            if not glVertexPointerd or not glDrawElements:
                return
            points = array(
                [
                    [0, 0, 0],
                    [0, 1, 0],
                    [1, 0.5, 0],
                    [1, 0, 0],
                    [1.5, 0.5, 0],
                    [1.5, 0, 0],
                ],
                dtype='d',
            )
            indices = array(
                range(len(points)),
                ['i', 'I'][int(bool(OpenGL.ERROR_ON_COPY))],  # test coercion if we can
            )
            d = vbo.VBO(points)
            glDisable(GL_CULL_FACE)
            glNormal3f(0, 0, 1)
            glColor3f(1, 1, 1)
            glEnableClientState(GL_VERTEX_ARRAY)
            try:
                for x in range(1, 255, 10):
                    d.bind()
                    try:
                        glVertexPointerd(d)
                        glDrawElements(
                            GL_LINE_LOOP, len(indices), GL_UNSIGNED_INT, indices
                        )
                    finally:
                        d.unbind()
                    lastPoint = array([[1.5, (1 / 255.0) * float(x), 0]])
                    d[-2:-1] = lastPoint
                    self.flip()
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    time.sleep(0.001)
            finally:
                glDisableClientState(GL_VERTEX_ARRAY)
            # bug report from Dan Helfman, delete shouldn't cause
            # errors if called explicitly
            d.delete()

        def test_glgetbufferparameter(self):
            self.require_vertex_arrays()
            buffer = glGenBuffers(1)
            vertex_array = glGenVertexArrays(1, buffer)
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            try:
                mapped = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_MAPPED)
                assert mapped == (
                    GL_FALSE if OpenGL.SIZE_1_ARRAY_UNPACK else [GL_FALSE]
                ), mapped
            finally:
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glDeleteVertexArrays(1, vertex_array)
                glDeleteBuffers(1, buffer)

        @pytest.mark.skipif(
            not OpenGL.SIZE_1_ARRAY_UNPACK,
            reason="Tests array unpack that is not configured",
        )
        def test_scalars_mapped_to_arrays(self):
            self.require_vertex_arrays()
            buffer = glGenBuffers(1)
            assert isscalar(buffer), type(buffer)
            glDeleteBuffers(1, buffer)

    def test_glbufferparameter_create(self):
        self.require_vertex_arrays()
        for create in [True, False]:
            buffer = glGenBuffers(1)
            vertex_array = glGenVertexArrays(1, buffer)
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            try:
                for param, expected in [
                    (GL_BUFFER_SIZE, 0),
                    (GL_BUFFER_MAPPED, GL_FALSE),
                    (GL_BUFFER_STORAGE_FLAGS, 0),
                    (GL_BUFFER_USAGE, GL_STATIC_DRAW),
                ]:
                    if create:
                        mapped = GLint(-1)
                        glGetBufferParameteriv(GL_ARRAY_BUFFER, param, mapped)
                        assert mapped.value == expected, (param, mapped, expected)
                    else:
                        mapped = glGetBufferParameteriv(GL_ARRAY_BUFFER, param)
                        # every one of these pnames is a single value; with
                        # SIZE_1_ARRAY_UNPACK the result is unpacked to a scalar.
                        # (GL_BUFFER_USAGE used to need [0] only because its size
                        # was wrongly (4,) -- clobbered by GL_OBJECT_BUFFER_USAGE_ATI
                        # sharing enum value 0x8765; that is fixed in glgetsizes.csv.)
                        if OpenGL.SIZE_1_ARRAY_UNPACK:
                            assert mapped == expected, (param, mapped, expected)
                        else:
                            assert mapped[0] == expected, (
                                param,
                                mapped[0],
                                expected,
                            )
            finally:
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glDeleteVertexArrays(1, vertex_array)
                glDeleteBuffers(1, buffer)

    # numpy-only: this guards numpy's dtype-mismatch *copy* behaviour.  The
    # ctypes no-numpy path never copies on asArray (it returns the array
    # unchanged), so there is no shrinking coercion to detect and the "must
    # raise" case cannot arise.  Define the test only when numpy is present,
    # matching the module's other array-dependent tests.
    if array:

        def test_glgetbuffersubdata_output_array(self):
            """Pass-in output arrays for glGetBufferSubData must be filled or rejected.

            A correctly-typed (ubyte) output array is filled in place. A
            mismatched-dtype array would be coerced to a *copy* (the GL result
            written into the copy, never reaching the caller's buffer, and
            truncated to the wrong element count), so the wrapper must raise
            instead of silently returning zeroes -- the reported bug.
            """
            if not glGenBuffers:
                return
            src = array([0x04030201, 0x08070605, 0x0C0B0A09], dtype='uint32')
            nbytes = int(src.nbytes)
            buf = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            try:
                glBufferData(GL_ARRAY_BUFFER, nbytes, src, GL_STATIC_DRAW)

                # correct-type output buffer: filled in place, bytes match.
                out = array([0] * nbytes, dtype='uint8')
                glGetBufferSubData(GL_ARRAY_BUFFER, 0, nbytes, out)
                assert (out.view('uint32') == src).all(), list(out)

                # mismatched dtype would silently lose the result -> must raise.
                with pytest.raises((TypeError, ValueError)):
                    glGetBufferSubData(GL_ARRAY_BUFFER, 0, nbytes,
                                       array([0, 0, 0], dtype='uint32'))
            finally:
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glDeleteBuffers(1, buf)

    def test_fbo(self):
        """Test that we support framebuffer objects

        http://www.gamedev.net/reference/articles/article2331.asp
        """
        if not glGenFramebuffers:
            print('No Frame Buffer Support!')
            return False
        width = height = 128
        fbo = glGenFramebuffers(1)
        with self.framebuffer(fbo):
            depthbuffer = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, depthbuffer)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthbuffer
            )

            img = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, img)
            # NOTE: these lines are *key*, without them you'll likely get an unsupported format error,
            # ie. GL_FRAMEBUFFER_UNSUPPORTED
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGB8,
                width,
                height,
                0,
                GL_RGB,
                GL_INT,
                None,  # no data transferred
            )
            glFramebufferTexture2D(
                GL_FRAMEBUFFER,
                GL_COLOR_ATTACHMENT0,
                GL_TEXTURE_2D,
                img,
                0,  # mipmap level, normally 0
            )
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            assert status == GL_FRAMEBUFFER_COMPLETE, status
            glPushAttrib(GL_VIEWPORT_BIT)  # viewport is shared with the main context
            try:
                glViewport(0, 0, width, height)

                # rendering to the texture here...
                glColor3f(1, 0, 0)
                glNormal3f(0, 0, 1)
                glBegin(GL_QUADS)
                for v in [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]]:
                    glColor3f(*v)
                    glVertex3d(*v)
                glEnd()
            finally:
                glPopAttrib()
                # restore viewport

        glBindTexture(GL_TEXTURE_2D, img)

        glEnable(GL_TEXTURE_2D)

        # rendering with the texture here...
        glColor3f(1, 1, 1)
        glNormal3f(0, 0, 1)
        glDisable(GL_LIGHTING)
        glBegin(GL_QUADS)
        try:
            for v in [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]]:
                glTexCoord2f(*v[:2])
                glVertex3d(*v)
        finally:
            glEnd()

    def test_gl_1_2_support(self):
        if glBlendColor:
            glBlendColor(0.3, 0.4, 1.0, 0.3)
            print('OpenGL 1.2 support')

    if array:

        def test_glmultidraw(self):
            """Test that glMultiDrawElements works, uses glDrawElements"""
            if glMultiDrawElements:
                points = array(
                    [(i, 0, 0) for i in range(8)] + [(i, 1, 0) for i in range(8)], 'd'
                )
                indices = array(
                    [
                        [
                            0,
                            8,
                            9,
                            1,
                            2,
                            10,
                            11,
                            3,
                        ],
                        [4, 12, 13, 5, 6, 14, 15, 7],
                    ],
                    'B',
                )
                index_pointers = arrays.GLvoidpArray.zeros((2,))
                index_pointers[0] = arrays.GLbyteArray.dataPointer(indices)
                index_pointers[1] = arrays.GLbyteArray.dataPointer(indices[1])
                counts = [len(x) for x in indices]
                if OpenGL.ERROR_ON_COPY:
                    counts = (GLuint * len(counts))(*counts)
                glEnableClientState(GL_VERTEX_ARRAY)
                glDisableClientState(GL_COLOR_ARRAY)
                glDisableClientState(GL_NORMAL_ARRAY)
                try:
                    glVertexPointerd(points)
                    glDisable(GL_LIGHTING)
                    try:
                        glMultiDrawElements(
                            GL_QUAD_STRIP, counts, GL_UNSIGNED_BYTE, index_pointers, 2
                        )
                    finally:
                        glEnable(GL_LIGHTING)
                finally:
                    glDisableClientState(GL_VERTEX_ARRAY)
            else:
                print('No multi_draw_arrays support')

    def test_glDrawBuffers_list(self):
        """Test that glDrawBuffers with list argument doesn't crash"""
        if not glDrawBuffers:
            return
        a_type = GLenum * 2
        args = a_type(
            GL_COLOR_ATTACHMENT0,
            GL_COLOR_ATTACHMENT1,
        )
        try:
            glDrawBuffers(2, args)
        except GLError as err:
            assert err.err == GL_INVALID_OPERATION, err

    def test_glDrawBuffers_list_valid(self):
        """Test that glDrawBuffers with list argument where value is set"""
        if not glGenFramebuffers:
            return
        if not glDrawBuffers:
            return
        previous = glGetIntegerv(GL_READ_BUFFER)
        fbo = glGenFramebuffers(1)
        with self.framebuffer(fbo):
            img1, img2 = glGenTextures(2)
            for img in img1, img2:
                glBindTexture(GL_TEXTURE_2D, img)
                glTexImage2D(
                    GL_TEXTURE_2D,
                    0,
                    GL_RGB8,
                    300,
                    300,
                    0,
                    GL_RGB,
                    GL_INT,
                    None,  # no data transferred
                )

            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, img1, 0
            )
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, img2, 0
            )
            a_type = GLenum * 2
            drawingBuffers = a_type(
                GL_COLOR_ATTACHMENT0,
                GL_COLOR_ATTACHMENT1,
            )
            glDrawBuffers(2, drawingBuffers)
            try:
                checkFramebufferStatus()
            except error.GLError:
                pass
            else:
                glReadBuffer(GL_COLOR_ATTACHMENT1)
                pixels = glReadPixels(0, 0, 10, 10, GL_RGB, GL_UNSIGNED_BYTE)
                assert len(pixels) == 300, len(pixels)

        # Back on the framebuffer the fixture drew into, so the buffer read off
        # it at the start is one it still accepts.
        glReadBuffer(previous)

    def test_get_version(self):
        from OpenGL.extensions import hasGLExtension

        if hasGLExtension('GL_VERSION_GL_2_0'):
            assert glShaderSource
            assert glUniform1f
        else:
            assert not glShaderSource
            assert not glUniform1f

    def test_lookupint(self):
        from OpenGL.raw.GL import _lookupint

        if GLQuerier.pullVersion() < [2]:
            return
        l = _lookupint.LookupInt(GL_NUM_COMPRESSED_TEXTURE_FORMATS, GLint)
        result = int(l)
        if not os.environ.get('TRAVIS'):
            assert (
                result
            ), "No compressed textures on this platform? that seems unlikely"
        else:
            "Travis xvfb doesn't normally have compressed textures, possible upgrade?"

    def test_glget(self):
        """Test that we can run glGet... on registered constants without crashing..."""
        from OpenGL.raw.GL import _glgets

        get_items = sorted(_glgets._glget_size_mapping.items())
        for key, value in get_items:
            # There are glGet values that will cause a crash during cleanup
            # GL_ATOMIC_COUNTER_BUFFER_BINDING 0x92c1 crashes/segfaults
            if key >= 0x8DF9 and key <= 0x8E23:
                continue
            if key >= 0x92BE and key <= 0x92C9:
                continue
            # print( 'Trying glGetFloatv( 0x%x )'%(key,))
            try:
                result = glGetFloatv(key)
            except error.GLError as err:
                if err.err == GL_INVALID_ENUM:
                    pass
                elif err.err == GL_INVALID_OPERATION:
                    if key == 0x882D:  # gl draw buffer
                        pass
                else:
                    raise
            else:
                if value == (1,) and OpenGL.SIZE_1_ARRAY_UNPACK:
                    try:
                        result = float(result)
                    except TypeError as err:
                        err.args += (result, key)
                        raise
                else:
                    assert ArrayDatatype.dimensions(result) == value, (
                        result,
                        ArrayDatatype.dimensions(result),
                        value,
                    )

    def test_max_compute_work_group_invocations(self):
        from OpenGL.extensions import hasGLExtension

        if hasGLExtension('GL_ARB_compute_shader'):
            assert glGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)

    def test_glCallLists_twice2(self):
        """SF#2829309 report that glCallLists doubles operation"""
        glRenderMode(GL_RENDER)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 10.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -3)
        first = glGenLists(2)
        second = first + 1

        glNewList(first, GL_COMPILE_AND_EXECUTE)
        glInitNames()
        if not OpenGL.ERROR_ON_COPY:
            glCallLists([second])  # replace with gCallList(2)
        else:
            lists = (GLuint * 1)()
            lists[0] = second
            glCallLists(lists)
        # glCallList(second)
        glEndList()

        glNewList(second, GL_COMPILE)
        glPushName(1)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        glEndList()
        glCallList(second)
        glPopName()
        depth = glGetIntegerv(GL_NAME_STACK_DEPTH)
        assert depth in (
            0,
            (0,),
        ), depth  # have popped, but even then, were' not in the mode...

        glSelectBuffer(100)
        glRenderMode(GL_SELECT)
        # ``first`` is the COMPILE_AND_EXECUTE list that runs glInitNames then
        # glCallLists([second]); ``second`` pushes a single name.  glGenLists
        # does not necessarily hand back id 1 (other tests share this context),
        # so call ``first`` explicitly rather than the literal list 1.
        glCallList(first)
        depth = glGetIntegerv(GL_NAME_STACK_DEPTH)
        assert depth in (1, (1,)), depth  # should have a single record
        glPopName()
        records = glRenderMode(GL_RENDER)
        # reporter says sees two records, Linux sees 0, Win32 sees 1 :(
        assert len(records) == 1, records

    def test_orinput_handling(self):
        self.require_vertex_arrays()
        x = glGenVertexArrays(1)
        x = int(x)  # check that we got x as an integer-compatible value
        x2 = GLuint()
        r_value = glGenVertexArrays(1, x2)
        assert x2.value, x2.value
        assert r_value

        color = glGetFloatv(GL_FOG_COLOR)
        color2 = (GLfloat * 4)()
        glGetFloatv(GL_FOG_COLOR, color2)
        for a, b in zip(color, color2):
            assert a == b, (color, color2)

    def test_get_read_fb_binding(self):
        if GLQuerier.pullVersion() < [3]:
            return
        glGetInteger(GL_READ_FRAMEBUFFER_BINDING)

    def test_shader_compile_string(self):
        if not glCreateShader:
            return None
        shader = glCreateShader(GL_VERTEX_SHADER)

        def glsl_version():
            """Parse GL_SHADING_LANGUAGE_VERSION into [int(major),int(minor)]"""
            version = glGetString(GL_SHADING_LANGUAGE_VERSION)
            version = version.split(as_8_bit(' '))[0]
            version = [int(x) for x in version.split(as_8_bit('.'))[:2]]
            return version

        if glsl_version() < [3, 3]:
            return
        SAMPLE_SHADER = '''#version 330
        void main() { gl_Position = vec4(0,0,0,0);}'''
        if OpenGL.ERROR_ON_COPY:
            SAMPLE_SHADER = as_8_bit(SAMPLE_SHADER)
        glShaderSource(shader, SAMPLE_SHADER)
        glCompileShader(shader)
        if not bool(glGetShaderiv(shader, GL_COMPILE_STATUS)) == True:
            print('Info log:')
            print(glGetShaderInfoLog(shader))
            assert False, """Failed to compile"""

    def test_gen_framebuffers_twice(self):
        if not glGenFramebuffersEXT:
            return
        glGenFramebuffersEXT(1)
        f1 = glGenFramebuffersEXT(1)
        f2 = glGenFramebuffersEXT(1)
        assert f1 != f2, (f1, f2)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, f2)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)

    def test_compressed_data(self):
        from OpenGL.extensions import hasGLExtension

        if hasGLExtension('GL_EXT_texture_compression_s3tc'):
            from OpenGL.GL.EXT import texture_compression_s3tc as s3tc

            texture = glGenTextures(1)
            glEnable(GL_TEXTURE_2D)
            image_type = GLubyte * 256 * 256
            image = image_type()
            glCompressedTexImage2D(
                GL_TEXTURE_2D,
                0,
                s3tc.GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
                256,
                256,
                0,
                # 256*256*1,
                image,
            )
            assert texture


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
