/* Entry points whose friendly behaviour is a computation rather than a
 * description, written by hand and registered beside the generated stubs.
 *
 * The generator names these in cdispatch.handwritten and emits their metadata
 * and table entry pointing here, so a hand-written entry point is reached
 * exactly as a generated one is.
 */
#include "pygl.h"

/* ------------------------------------------------------------------ *
 * glShaderSource(shader, string)
 *
 * The C entry point takes four arguments -- shader, count, an array of
 * pointers to the sources, and an array of their lengths -- and the friendly
 * form takes two, computing the other two from what it was given.  A caller
 * may pass one string or a sequence of them, in any of the forms
 * OpenGL._string_array accepts.
 * ------------------------------------------------------------------ */

/* What one call assembles, and owns until pygl_sources_free.  It is the same
 * bargain PyGLBuf strikes for a generated stub: a strong reference plus the
 * blocks pointing into it, released on every path out. */
typedef struct {
    PyObject *owner;   /* the list of bytes objects keeping the text alive */
    const char **text; /* this struct's own memory, pointing into that list */
    int *lengths;      /* likewise */
    Py_ssize_t count;
} PyGLSources;

/* Give up all three, and leave the struct able to take it again.  Safe on a
 * struct pygl_sources_build zeroed and then failed in, which is how the
 * allocation failure below unwinds. */
static void pygl_sources_free(PyGLSources *sources)
{
    PyMem_Free(sources->text);
    sources->text = NULL;
    PyMem_Free(sources->lengths);
    sources->lengths = NULL;
    Py_CLEAR(sources->owner);
}

/* Fill `sources` from whatever the caller passed.  On success it owns the list
 * and the two blocks and the caller must free it; on failure it owns nothing,
 * so a stub that returns straight out leaks none of it.
 *
 * The strings arrive through pygl_string_list, which is where every entry
 * point taking an array of strings gets them: what counts as one is a single
 * rule in OpenGL._string_array, and a hand-written body restating it in C
 * would be a second answer to the same question. */
static int pygl_sources_build(const char *name, PyObject *argument,
                              PyGLSources *sources)
{
    Py_ssize_t index;

    sources->owner = NULL;
    sources->text = NULL;
    sources->lengths = NULL;
    sources->count = 0;

    sources->owner = pygl_string_list(name, argument);
    if (sources->owner == NULL) {
        return -1;
    }
    sources->count = PyList_GET_SIZE(sources->owner);
    if (sources->count == 0) {
        return 0;
    }
    sources->text = PyMem_Calloc((size_t)sources->count, sizeof(const char *));
    sources->lengths = PyMem_Calloc((size_t)sources->count, sizeof(int));
    if (sources->text == NULL || sources->lengths == NULL) {
        pygl_sources_free(sources);
        PyErr_NoMemory();
        return -1;
    }
    for (index = 0; index < sources->count; index++) {
        PyObject *item = PyList_GET_ITEM(sources->owner, index);
        sources->text[index] = PyBytes_AS_STRING(item);
        sources->lengths[index] = (int)PyBytes_GET_SIZE(item);
    }
    return 0;
}

PyObject *pygl_hand_glShaderSource(PyObject *_self, PyObject *const *_a,
                                   size_t _nargsf, PyObject *_kwnames)
{
    GLProc *self = (GLProc *)_self;
    PyGLSources sources;
    Py_ssize_t _nargs = PyVectorcall_NARGS(_nargsf);
    unsigned int shader;
    void *_fp;

    /* As a generated stub does: a keyword reaches here as a positional in _a
     * with its name in _kwnames, so ignoring _kwnames would take
     * glShaderSource(shader, string=s) as a one-argument call and report the
     * arity rather than the keyword. */
    PYGL_NO_KEYWORDS();
    if (_nargs != 2) {
        return pygl_arity_error(self, 2, _nargs);
    }
    shader = (unsigned int)PyLong_AsUnsignedLongMask(_a[0]);
    if (PyErr_Occurred()) {
        return NULL;
    }
    if (pygl_sources_build(self->info->name, _a[1], &sources) < 0) {
        return NULL;
    }
    _fp = pygl_slot(self);
    if (_fp == NULL) {
        pygl_sources_free(&sources);
        return NULL;
    }
    ((void (*)(unsigned int, int, const char *const *, const int *))_fp)(
        shader, (int)sources.count, sources.text, sources.lengths);
    pygl_sources_free(&sources);
    if (pygl_check_needed(self) && pygl_check_error(self, _a, _nargs) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}
