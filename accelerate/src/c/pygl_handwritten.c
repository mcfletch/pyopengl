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
 * may pass one string or a sequence of them, as `str` or as `bytes`.
 * ------------------------------------------------------------------ */

typedef struct {
    PyObject *owner;   /* the list of bytes objects keeping the text alive */
    const char **text;
    int *lengths;
    Py_ssize_t count;
} PyGLSources;

static void pygl_sources_free(PyGLSources *sources)
{
    PyMem_Free(sources->text);
    PyMem_Free(sources->lengths);
    Py_CLEAR(sources->owner);
}

/* Normalise the argument to a list of bytes, whatever shape it arrived in. */
static PyObject *pygl_source_list(PyObject *argument)
{
    PyObject *list, *item;

    if (PyUnicode_Check(argument) || PyBytes_Check(argument)) {
        list = PyList_New(1);
        if (list == NULL) {
            return NULL;
        }
        item = PyUnicode_Check(argument)
                   ? PyUnicode_AsUTF8String(argument)
                   : Py_NewRef(argument);
        if (item == NULL) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, 0, item);
        return list;
    }

    {
        PyObject *sequence = PySequence_Fast(
            argument, "glShaderSource: expected a string or a sequence of them");
        Py_ssize_t index, count;
        if (sequence == NULL) {
            return NULL;
        }
        count = PySequence_Fast_GET_SIZE(sequence);
        list = PyList_New(count);
        if (list == NULL) {
            Py_DECREF(sequence);
            return NULL;
        }
        for (index = 0; index < count; index++) {
            PyObject *entry = PySequence_Fast_GET_ITEM(sequence, index);
            if (PyUnicode_Check(entry)) {
                item = PyUnicode_AsUTF8String(entry);
            } else if (PyBytes_Check(entry)) {
                item = Py_NewRef(entry);
            } else {
                PyErr_Format(PyExc_TypeError,
                             "glShaderSource: source %zd is %s, not a string",
                             index, Py_TYPE(entry)->tp_name);
                item = NULL;
            }
            if (item == NULL) {
                Py_DECREF(list);
                Py_DECREF(sequence);
                return NULL;
            }
            PyList_SET_ITEM(list, index, item);
        }
        Py_DECREF(sequence);
        return list;
    }
}

static int pygl_sources_build(PyObject *argument, PyGLSources *sources)
{
    Py_ssize_t index;

    sources->owner = NULL;
    sources->text = NULL;
    sources->lengths = NULL;
    sources->count = 0;

    sources->owner = pygl_source_list(argument);
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

PyObject *pygl_hand_glShaderSource(GLProc *self, PyObject *const *_a,
                                   size_t _nargsf, PyObject *_kwnames)
{
    PyGLSources sources;
    Py_ssize_t _nargs = PyVectorcall_NARGS(_nargsf);
    unsigned int shader;
    void *_fp;

    if (_nargs != 2) {
        return pygl_arity_error(self, 2, _nargs);
    }
    shader = (unsigned int)PyLong_AsUnsignedLongMask(_a[0]);
    if (PyErr_Occurred()) {
        return NULL;
    }
    if (pygl_sources_build(_a[1], &sources) < 0) {
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
