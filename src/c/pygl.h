/* PyOpenGL C dispatch layer -- runtime declarations and the macro vocabulary
 * the generated entry points are written in.
 *
 * Design: plans/C-DISPATCH.md.  The short version: one C function per registry
 * command, reached through a per-context table of function pointers, called
 * through CPython's vectorcall protocol so that dispatch costs what calling an
 * empty Python function costs.
 */
#ifndef PYGL_H
#define PYGL_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stddef.h>
#include <stdint.h>

#if defined(__GNUC__) || defined(__clang__)
#define PYGL_LIKELY(x) __builtin_expect(!!(x), 1)
#define PYGL_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define PYGL_LIKELY(x) (x)
#define PYGL_UNLIKELY(x) (x)
#endif

/* ------------------------------------------------------------------ *
 * GL types
 *
 * Declared here rather than included from a system header so that the
 * generated code compiles identically everywhere and does not depend on
 * which GL headers happen to be installed.
 * ------------------------------------------------------------------ */
typedef unsigned int PyGL_GLenum;
typedef unsigned char PyGL_GLboolean;
typedef unsigned int PyGL_GLbitfield;
typedef signed char PyGL_GLbyte;
typedef short PyGL_GLshort;
typedef int PyGL_GLint;
typedef int PyGL_GLsizei;
typedef unsigned char PyGL_GLubyte;
typedef unsigned short PyGL_GLushort;
typedef unsigned int PyGL_GLuint;
typedef float PyGL_GLfloat;
typedef float PyGL_GLclampf;
typedef double PyGL_GLdouble;
typedef double PyGL_GLclampd;
typedef int PyGL_GLfixed;
typedef int64_t PyGL_GLint64;
typedef uint64_t PyGL_GLuint64;
typedef intptr_t PyGL_GLintptr;
typedef ptrdiff_t PyGL_GLsizeiptr;
typedef void *PyGL_GLsync;
typedef void *PyGL_opaque;

/* GLhandleARB is void * on macOS and unsigned int everywhere else.  It is the
 * only such divergence in the registry, and it has its own test. */
#if defined(__APPLE__)
typedef void *PyGL_GLhandleARB;
#define PYGL_HANDLE_IS_POINTER 1
#else
typedef unsigned int PyGL_GLhandleARB;
#define PYGL_HANDLE_IS_POINTER 0
#endif

/* ------------------------------------------------------------------ *
 * array element types
 *
 * The fast path is a match test, never a validation: a buffer whose format
 * matches is used directly, and anything else -- a different element type, a
 * non-contiguous buffer, an object with no buffer protocol at all -- falls
 * through to ArrayDatatype and the format-handler registry, which behaves
 * exactly as it does today.  A new element type is a new row here plus a new
 * ArrayDatatype subclass; it needs no new C and no change to any stub.
 * ------------------------------------------------------------------ */
typedef struct {
    /* struct-module format codes this element accepts.  '\0' in primary means
     * nothing ever matches, so every call takes the Python path.  '*' means
     * any contiguous buffer is acceptable, which is what a void * parameter
     * promises. */
    char primary;
    char alt1;
    char alt2;
    uint8_t itemsize;
    /* index into the array-type objects resolved from OpenGL.arrays at init */
    uint16_t array_index;
    const char *name;
} PyGLElement;

/* ------------------------------------------------------------------ *
 * command metadata
 * ------------------------------------------------------------------ */
enum {
    PYGL_API_GL = 0,
    PYGL_API_GLES1,
    PYGL_API_GLES2,
    PYGL_API_GLES3,
    PYGL_API_GLSC2,
    PYGL_API_GLX,
    PYGL_API_WGL,
    PYGL_API_EGL,
    PYGL_API_COUNT
};

/* What a stub turns the driver's answer into.  Assigning restype asks for a
 * different conversion; assigning the one already implemented changes nothing
 * and is accepted without demoting the entry point. */
enum {
    PYGL_RET_VOID = 0,
    PYGL_RET_INT,
    PYGL_RET_BYTES,
    PYGL_RET_FLOAT,
    PYGL_RET_OPAQUE,
    PYGL_RET_ADDRESS
};

typedef struct {
    const char *name;
    const char *doc;            /* signature line, plus purpose where cleared */
    const char *text_signature; /* so inspect.signature() answers */
    const char *const *arg_names;
    const char *extension; /* the feature or extension that requires it */
    uint16_t arg_count;
    uint16_t slot; /* index into every context's dispatch table */
    uint8_t api;
    uint8_t deprecated;
    uint8_t required_args; /* arguments a caller must supply */
    uint8_t return_kind;
    /* Set for an entry point written by hand rather than generated.  Its
     * friendly behaviour is already complete, so a customisation call that
     * restates it changes nothing rather than demoting to ctypes. */
    uint8_t hand_written;
} PyGLCommand;

/* ------------------------------------------------------------------ *
 * per-context dispatch
 *
 * N contexts live in one process, each holding its own function pointer for
 * every entry point.  One GLProc object exists per command process-wide and
 * holds a slot index, never an address, so a binding a client hoisted into a
 * local before a context switch still dispatches correctly after it.
 * ------------------------------------------------------------------ */
enum {
    PYGL_SLOT_UNRESOLVED = 0, /* never looked up in this context */
    PYGL_SLOT_ABSENT = 1,     /* looked up, this context does not have it */
    PYGL_SLOT_MIN_REAL = 2
};

/* per-slot flag bits */
enum {
    PYGL_F_CHECK_ERRORS = 1 << 0,
};

typedef struct PyGLDispatch {
    void **slots;
    uint8_t *flags;
    void *handle;         /* the platform context handle this table serves */
    unsigned generation;  /* guards a handle the driver reused */
    int is_null_context;  /* the table used when no context is current */
    struct PyGLDispatch *next;
} PyGLDispatch;

#if defined(_MSC_VER)
#define PYGL_THREAD_LOCAL __declspec(thread)
#else
#define PYGL_THREAD_LOCAL __thread
#endif

extern PYGL_THREAD_LOCAL PyGLDispatch *pygl_current;

/* ------------------------------------------------------------------ *
 * the callable
 * ------------------------------------------------------------------ */
typedef struct {
    PyObject_HEAD vectorcallfunc vectorcall;
    const PyGLCommand *info;
    /* Set only when the entry point has been demoted to ctypes by assigning
     * errcheck or argtypes.  Demotion is per function, for the life of the
     * process. */
    PyObject *ctypes_callable;
    PyObject *errcheck;
    PyObject *weakreflist;
    /* Clients set attributes on bindings -- glget.py sets __doc__, and third
     * party code annotates them -- so an entry point carries an instance
     * dictionary.  Nothing on the call path reads it. */
    PyObject *doc_override;
    /* The friendly modules clear `extension` on a few entry points so that
     * they resolve as core rather than through an extension check. */
    PyObject *extension_override;
    int has_extension_override;
    PyObject *dict;
} GLProc;

extern PyTypeObject PyGLProc_Type;

/* ------------------------------------------------------------------ *
 * runtime entry points the generated code calls
 * ------------------------------------------------------------------ */
typedef struct {
    Py_buffer view;
    PyObject *owner; /* strong reference when the slow path converted */
    void *pointer;
    int have_view;
} PyGLBuf;

/* Resolve a slot in the current context, or raise.  Never inlined: it is the
 * once-per-context-per-entry-point path. */
void *pygl_slot_slow(GLProc *self);

static inline void *pygl_slot(GLProc *self)
{
    void *fp = pygl_current->slots[self->info->slot];
    if (PYGL_LIKELY((uintptr_t)fp >= PYGL_SLOT_MIN_REAL)) {
        return fp;
    }
    return pygl_slot_slow(self);
}

static inline int pygl_wants_error_check(GLProc *self)
{
    return pygl_current->flags[self->info->slot] & PYGL_F_CHECK_ERRORS;
}

/* How errors are noticed.  GL_KHR_debug reports them through a callback the
 * driver invokes during the call, so checking becomes a read of a flag rather
 * than a glGetError round trip. */
enum { PYGL_ERRORS_GETERROR = 0, PYGL_ERRORS_DEBUG = 1 };
extern int pygl_error_mode;
extern PYGL_THREAD_LOCAL int pygl_debug_pending;

int pygl_check_error(GLProc *self);

static inline int pygl_check_needed(GLProc *self)
{
    if (pygl_error_mode == PYGL_ERRORS_DEBUG) {
        return pygl_debug_pending;
    }
    return pygl_current->flags[self->info->slot] & PYGL_F_CHECK_ERRORS;
}
PyObject *pygl_arity_error(GLProc *self, Py_ssize_t want, Py_ssize_t got);
PyObject *pygl_arity_range_error(GLProc *self, Py_ssize_t low, Py_ssize_t high,
                                 Py_ssize_t got);
void pygl_argument_error(GLProc *self, Py_ssize_t index, const char *expected);

/* Acquire an input array.  Matching buffers are used directly; everything else
 * is handed to ArrayDatatype, which converts exactly as it does today. */
int pygl_array_in(GLProc *self, PyObject *object, const PyGLElement *element,
                  Py_ssize_t index, PyGLBuf *out);
/* As above, and additionally check the element count. */
int pygl_array_in_sized(GLProc *self, PyObject *object, const PyGLElement *element,
                        Py_ssize_t index, Py_ssize_t expected, PyGLBuf *out);
/* One pname's output size, from the generated _glgets table. */
typedef struct {
    uint32_t pname;
    uint16_t dim0;
    uint16_t dim1;
    uint32_t lookup; /* non-zero: query this pname for the element count */
} PyGLGetSize;

/* Allocate an output array sized from the pname table, or accept the caller's.
 * `count` receives the element count, for the return-value unpacking. */
int pygl_array_out_glget(GLProc *self, PyObject *object, const PyGLElement *element,
                         Py_ssize_t index, unsigned int pname,
                         const PyGLGetSize *table, Py_ssize_t table_count,
                         PyGLBuf *out, Py_ssize_t *count);

/* Allocate an output array of `count` elements, or accept the caller's. */
int pygl_array_out(GLProc *self, PyObject *object, const PyGLElement *element,
                   Py_ssize_t index, Py_ssize_t count, PyGLBuf *out);
void pygl_release(PyGLBuf *buffer);

/* Return-value conversion.  The rule is that the C layer returns the same
 * Python object the ctypes layer returns today. */
PyObject *pygl_bytes_or_none(const char *value);
PyObject *pygl_address_or_none(void *value);
PyObject *pygl_opaque(void *value, const char *type_name);

/* The output-array return.  A one-element result is unpacked to a scalar,
 * which is what the friendly API does today. */
PyObject *pygl_output_value(PyGLBuf *buffer, const PyGLElement *element,
                            Py_ssize_t count);

/* Several outputs compose into a tuple, in the order they were declared. */
typedef struct {
    int slot;
    const PyGLElement *element;
    Py_ssize_t count;
} PyGLOutput;

PyObject *pygl_output_tuple(PyGLBuf *buffers, const PyGLOutput *outputs,
                            Py_ssize_t count);

/* The generated tables register themselves through these. */
typedef struct {
    const PyGLCommand *info;
    vectorcallfunc stub;
} PyGLEntry;

/* Build one GLProc per entry and file it under (api, name) in the module's
 * entry-point mapping.  The Python side reads that mapping when it installs
 * the C implementation over the ctypes one. */
int pygl_register_entries(PyObject *mapping, const PyGLEntry *entries);
int pygl_set_command_count(Py_ssize_t count);
PyObject *pygl_make_proc(const PyGLCommand *command, vectorcallfunc stub);

/* ------------------------------------------------------------------ *
 * the macro vocabulary
 * ------------------------------------------------------------------ */

#define PYGL_ARITY(n)                                                          \
    Py_ssize_t _nargs = PyVectorcall_NARGS(_nargsf);                           \
    if (PYGL_UNLIKELY(_nargs != (n)))                                          \
    return pygl_arity_error(self, (n), _nargs)

/* For the variadic entry points, which accept a range of argument counts. */
#define PYGL_ARITY_RANGE(low, high)                                            \
    Py_ssize_t _nargs = PyVectorcall_NARGS(_nargsf);                           \
    if (PYGL_UNLIKELY(_nargs < (low) || _nargs > (high)))                      \
    return pygl_arity_range_error(self, (low), (high), _nargs)

#define PYGL_FRAME(n)                                                          \
    PyGLBuf _bufs[(n)];                                                        \
    int _nb = 0

#define PYGL_CLEANUP()                                                         \
    while (_nb) {                                                              \
        pygl_release(&_bufs[--_nb]);                                           \
    }

/* Scalar conversions.  None of them can fail destructively, so a single
 * PyErr_Occurred() after the group replaces a branch per argument. */
#define PYGL_U(i, name) PyGL_GLuint name = (PyGL_GLuint)PyLong_AsUnsignedLongMask(_a[i])
#define PYGL_I(i, name) PyGL_GLint name = (PyGL_GLint)PyLong_AsLong(_a[i])
#define PYGL_SZ(i, name) PyGL_GLsizei name = (PyGL_GLsizei)PyLong_AsLong(_a[i])
#define PYGL_F(i, name) PyGL_GLfloat name = (PyGL_GLfloat)pygl_as_double(_a[i])
#define PYGL_D(i, name) PyGL_GLdouble name = (PyGL_GLdouble)pygl_as_double(_a[i])
#define PYGL_B(i, name) PyGL_GLboolean name = (PyGL_GLboolean)pygl_as_boolean(_a[i])
#define PYGL_I64(i, name) PyGL_GLint64 name = (PyGL_GLint64)PyLong_AsLongLong(_a[i])
#define PYGL_U64(i, name)                                                      \
    PyGL_GLuint64 name = (PyGL_GLuint64)PyLong_AsUnsignedLongLongMask(_a[i])
#define PYGL_IPTR(i, name) PyGL_GLintptr name = (PyGL_GLintptr)PyLong_AsSsize_t(_a[i])
#define PYGL_OPAQUE(i, name) void *name = pygl_as_pointer(_a[i])
#if PYGL_HANDLE_IS_POINTER
#define PYGL_HANDLE(i, name) PyGL_GLhandleARB name = pygl_as_pointer(_a[i])
#else
#define PYGL_HANDLE(i, name)                                                   \
    PyGL_GLhandleARB name = (PyGL_GLhandleARB)PyLong_AsUnsignedLongMask(_a[i])
#endif

#define PYGL_CONV_OK()                                                         \
    if (PYGL_UNLIKELY(PyErr_Occurred() != NULL))                               \
    goto _fail

#define PYGL_ARRAY_IN(i, name, element)                                        \
    if (PYGL_UNLIKELY(pygl_array_in(self, _a[i], (element), (i), &_bufs[_nb]) < 0))  \
        goto _fail;                                                            \
    void *name = _bufs[_nb++].pointer

#define PYGL_ARRAY_IN_SIZED(i, name, element, count)                           \
    if (PYGL_UNLIKELY(pygl_array_in_sized(self, _a[i], (element), (i), (count),      \
                                          &_bufs[_nb]) < 0))                   \
        goto _fail;                                                            \
    void *name = _bufs[_nb++].pointer

#define PYGL_ARRAY_OUT_GLGET(i, name, element, pname, table)                   \
    int name##_slot = _nb;                                                     \
    Py_ssize_t name##_count = 0;                                               \
    if (PYGL_UNLIKELY(pygl_array_out_glget(self, (i) < _nargs ? _a[i] : NULL,   \
                                           (element), (i), (pname), (table),   \
                                           (table##_count), &_bufs[_nb],       \
                                           &name##_count) < 0))                \
        goto _fail;                                                            \
    void *name = _bufs[_nb++].pointer

#define PYGL_ARRAY_OUT(i, name, element, count)                                \
    int name##_slot = _nb;                                                     \
    if (PYGL_UNLIKELY(pygl_array_out(self, (i) < _nargs ? _a[i] : NULL, (element),   \
                                     (i), (count), &_bufs[_nb]) < 0))          \
        goto _fail;                                                            \
    void *name = _bufs[_nb++].pointer

/* Load the slot for the current context and call through it. */
#define PYGL_CALL_V(signature, arguments)                                      \
    do {                                                                       \
        void *_fp = pygl_slot(self);                                           \
        if (PYGL_UNLIKELY(_fp == NULL))                                        \
            goto _fail;                                                        \
        ((void (*) signature)_fp) arguments;                                   \
    } while (0)

#define PYGL_CALL_R(result, type, signature, arguments)                        \
    type result;                                                               \
    do {                                                                       \
        void *_fp = pygl_slot(self);                                           \
        if (PYGL_UNLIKELY(_fp == NULL))                                        \
            goto _fail;                                                        \
        result = ((type(*) signature)_fp) arguments;                           \
    } while (0)

#define PYGL_CHECK()                                                           \
    if (PYGL_UNLIKELY(pygl_check_needed(self))) {                              \
        if (pygl_check_error(self) < 0)                                        \
            goto _fail;                                                        \
    }

/* ------------------------------------------------------------------ *
 * small conversions used by the macros
 * ------------------------------------------------------------------ */
static inline double pygl_as_double(PyObject *object)
{
    if (PyFloat_CheckExact(object)) {
        return PyFloat_AS_DOUBLE(object);
    }
    return PyFloat_AsDouble(object);
}

int pygl_boolean_slow(PyObject *object);

static inline int pygl_as_boolean(PyObject *object)
{
    if (object == Py_True) {
        return 1;
    }
    if (object == Py_False || object == Py_None) {
        return 0;
    }
    return pygl_boolean_slow(object);
}

void *pygl_pointer_slow(PyObject *object);

static inline void *pygl_as_pointer(PyObject *object)
{
    if (object == Py_None) {
        return NULL;
    }
    if (PyLong_CheckExact(object)) {
        return (void *)(uintptr_t)PyLong_AsUnsignedLongLongMask(object);
    }
    return pygl_pointer_slow(object);
}

#endif /* PYGL_H */
