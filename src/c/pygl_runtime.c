/* PyOpenGL C dispatch layer -- runtime.
 *
 * Holds the per-context dispatch tables, the GLProc callable, the array
 * marshalling helpers and the bridge back into Python for everything that is
 * not on the hot path.  The generated entry points in src/c/generated call
 * into this file through the macros in pygl.h.
 */
#include "pygl.h"

/* ------------------------------------------------------------------ *
 * module-level state
 * ------------------------------------------------------------------ */

/* Filled at import from OpenGL._dispatch.support. */
static PyObject *pygl_support = NULL;      /* the support module */
static PyObject *pygl_array_types = NULL;  /* list, indexed by array_index */
static PyObject *pygl_ctypes_argument_error = NULL;
static PyObject *pygl_null_function_error = NULL;
static PyObject *pygl_no_context_error = NULL;
static PyObject *pygl_gl_error = NULL;
static PyObject *pygl_str_asArray = NULL;
static PyObject *pygl_str_dataPointer = NULL;
static PyObject *pygl_str_zeros = NULL;
/* ctypes._SimpleCData and ctypes._Pointer.  A c_void_p means the address it
 * holds, not the eight bytes it occupies, so these must never take the buffer
 * fast path -- ArrayDatatype is the authority on what they point at. */
static PyObject *pygl_ctypes_simple = NULL;
static PyObject *pygl_ctypes_pointer = NULL;

static Py_ssize_t pygl_command_count = 0;
static int pygl_error_slot = -1;
static int pygl_strict_context = 0;
static int pygl_array_size_checking = 1;
int pygl_context_checking = 0;
int pygl_context_tracking = PYGL_TRACK_NOTIFY;
/* OpenGL.SIZE_1_ARRAY_UNPACK: whether a one-element output is handed back as a
 * scalar rather than as an array of one. */
static int pygl_size_1_array_unpack = 1;
/* glGetError inside a glBegin/glEnd block is itself an invalid operation, so
 * error checking is suspended for the duration.  The ctypes path does this
 * through _ErrorChecker.onBegin/onEnd; this is the same switch. */
static int pygl_error_suspended = 0;

/* GL_KHR_debug reporting.  The driver calls pygl_debug_callback during the GL
 * call itself when GL_DEBUG_OUTPUT_SYNCHRONOUS is on, so the callback records
 * what happened and the stub's check becomes a read of `pygl_debug_pending`
 * rather than a glGetError round trip. */
int pygl_error_mode = PYGL_ERRORS_GETERROR;
PYGL_THREAD_LOCAL int pygl_debug_pending = 0;
#define PYGL_DEBUG_MESSAGE_MAX 1024
static PYGL_THREAD_LOCAL char pygl_debug_message[PYGL_DEBUG_MESSAGE_MAX];
static PYGL_THREAD_LOCAL unsigned int pygl_debug_id = 0;
/* The flag byte a freshly created context table starts every slot at, so that
 * OpenGL.ERROR_CHECKING means the same thing in a context created later. */
static uint8_t pygl_default_flags = 0;
/* The glGetError entry point, so the error check can resolve its own slot in a
 * context that has not called it yet. */
static PyObject *pygl_error_proc = NULL;

/* The platform's "which context is current" function, as a raw address, so the
 * strict-tracking mode does not pay a Python call.  Costs about 95ns on the
 * reference machine, which is why it is not on the default path. */
static void *(*pygl_get_current_context)(void) = NULL;

/* ------------------------------------------------------------------ *
 * per-context dispatch tables
 * ------------------------------------------------------------------ */

/* Used when the platform reports that no context is current. */
static PyGLDispatch pygl_null_table = {NULL, NULL, NULL, 0, 1, NULL};
/* Used when the platform offers no way to ask which context is current.  It
 * behaves as an ordinary table, because "we cannot tell" must not be reported
 * as "there is none". */
static PyGLDispatch pygl_default_table = {NULL, NULL, NULL, 0, 0, NULL};
PYGL_THREAD_LOCAL PyGLDispatch *pygl_current = &pygl_default_table;

static PyGLDispatch *pygl_tables = NULL; /* handle -> table, a short list */
static PyThread_type_lock pygl_tables_lock = NULL;

static PyGLDispatch *pygl_table_new(void *handle)
{
    PyGLDispatch *table = PyMem_Calloc(1, sizeof(PyGLDispatch));
    if (table == NULL) {
        return NULL;
    }
    table->slots = PyMem_Calloc((size_t)pygl_command_count, sizeof(void *));
    table->flags = PyMem_Calloc((size_t)pygl_command_count, sizeof(uint8_t));
    if (table->slots == NULL || table->flags == NULL) {
        PyMem_Free(table->slots);
        PyMem_Free(table->flags);
        PyMem_Free(table);
        return NULL;
    }
    if (pygl_default_flags) {
        memset(table->flags, pygl_default_flags, (size_t)pygl_command_count);
    }
    table->handle = handle;
    return table;
}

static void pygl_table_free(PyGLDispatch *table)
{
    PyMem_Free(table->slots);
    PyMem_Free(table->flags);
    PyMem_Free(table);
}

/* Look up or create the table for a context handle. */
static PyGLDispatch *pygl_table_for(void *handle)
{
    PyGLDispatch *table;
    if (handle == NULL) {
        return &pygl_null_table;
    }
    PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
    for (table = pygl_tables; table != NULL; table = table->next) {
        if (table->handle == handle) {
            PyThread_release_lock(pygl_tables_lock);
            return table;
        }
    }
    table = pygl_table_new(handle);
    if (table != NULL) {
        table->next = pygl_tables;
        pygl_tables = table;
    }
    PyThread_release_lock(pygl_tables_lock);
    return table == NULL ? &pygl_null_table : table;
}

/* Make `handle` the context this thread dispatches through. */
static int pygl_make_current(void *handle)
{
    PyGLDispatch *table = pygl_table_for(handle);
    if (table == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    pygl_current = table;
    return 0;
}

/* Re-read the current context from the platform.
 *
 * On the resolution slow path this asks the platform layer in Python, because
 * that is the only thing that knows which interface owns the current context:
 * a Linux process can hold GLX and EGL contexts at once, and asking the wrong
 * one answers "none".  It runs once per entry point per context, so the cost
 * of a Python call is not on any hot path.
 *
 * Strict tracking mode calls this on every call and cannot afford that, so it
 * uses the raw address of whichever interface was active when the layer was
 * configured. */
static void pygl_sync_context(void)
{
    void *handle;
    PyObject *answer;

    if (pygl_support == NULL) {
        return;
    }
    answer = PyObject_CallMethod(pygl_support, "current_context", NULL);
    if (answer == NULL) {
        PyErr_Clear();
        return;
    }
    handle = (void *)(uintptr_t)PyLong_AsUnsignedLongLong(answer);
    Py_DECREF(answer);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return;
    }
    if (handle != pygl_current->handle) {
        pygl_make_current(handle);
    }
}

/* The per-call form.  Uses the raw address of whichever interface was active
 * when the layer was configured, since it cannot afford a Python call.
 *
 * That address is chosen before any context exists, so on a system serving
 * both GLX and EGL it can be the wrong one -- and the wrong one answers "no
 * context" rather than failing, which would turn a live context into a
 * NoContext error.  A null answer is therefore checked against the platform
 * layer, which knows which interface owns the current context. */
static void pygl_sync_context_fast(void)
{
    void *handle;
    if (pygl_get_current_context == NULL) {
        pygl_sync_context();
        return;
    }
    handle = pygl_get_current_context();
    if (handle == NULL) {
        pygl_sync_context();
        return;
    }
    if (handle != pygl_current->handle) {
        pygl_make_current(handle);
    }
}

/* ------------------------------------------------------------------ *
 * slot resolution
 * ------------------------------------------------------------------ */

/* Entry points that are meaningful with no GL context current.  These are the
 * same exemptions the ctypes path's context check applies. */
static int pygl_needs_context(const PyGLCommand *command)
{
    const char *name = command->name;
    if (command->api == PYGL_API_GLX || command->api == PYGL_API_WGL ||
        command->api == PYGL_API_EGL) {
        /* The window-system APIs are how a context is made in the first place,
         * so they are meaningful with none current. */
        return 0;
    }
    if (strcmp(name, "glGetString") == 0 || strcmp(name, "glGetStringi") == 0 ||
        strcmp(name, "glGetIntegerv") == 0 || strcmp(name, "glGetError") == 0) {
        return 0;
    }
    return 1;
}

void *pygl_slot_slow(GLProc *self)
{
    const PyGLCommand *command = self->info;
    PyObject *result;
    void *address;
    unsigned long long value;

    /* Ask the platform which context is actually current *before* consulting
     * what this table remembers.  Reaching here is the
     * once-per-context-per-entry-point path, so it can afford the query, and
     * doing it first is what makes a missed make_current notification
     * self-correcting -- including the case where an entry point was probed
     * before any context existed and the answer was recorded against the
     * table used when there is none. */
    pygl_sync_context();

    if (pygl_context_checking && pygl_current->is_null_context &&
        pygl_needs_context(command)) {
        PyErr_Format(pygl_no_context_error,
                     "Attempt to call %s with no current OpenGL context",
                     command->name);
        return NULL;
    }
    if (pygl_current->slots[command->slot] == (void *)PYGL_SLOT_ABSENT) {
        PyErr_Format(pygl_null_function_error,
                     "Attempt to call an undefined function %s, check for bool(%s) "
                     "before calling",
                     command->name, command->name);
        return NULL;
    }
    if ((uintptr_t)pygl_current->slots[command->slot] >= PYGL_SLOT_MIN_REAL) {
        return pygl_current->slots[command->slot];
    }

    {
        const char *extension = command->extension ? command->extension : "";
        if (self->has_extension_override) {
            extension = self->extension_override
                            ? PyUnicode_AsUTF8(self->extension_override)
                            : "";
            if (extension == NULL) {
                return NULL;
            }
        }
        result = PyObject_CallMethod(pygl_support, "resolve", "sssi",
                                     command->name, extension, "",
                                     (int)command->api);
    }
    if (result == NULL) {
        return NULL;
    }
    if (result == Py_None) {
        Py_DECREF(result);
        /* "Absent" is only worth remembering when a context was current to
         * answer it.  Without one the answer says nothing about any real
         * context, and remembering it would outlive the reason for it. */
        if (pygl_current->handle != NULL) {
            pygl_current->slots[command->slot] = (void *)PYGL_SLOT_ABSENT;
        }
        PyErr_Format(pygl_null_function_error,
                     "Attempt to call an undefined function %s, check for bool(%s) "
                     "before calling",
                     command->name, command->name);
        return NULL;
    }
    value = PyLong_AsUnsignedLongLong(result);
    Py_DECREF(result);
    if (PyErr_Occurred()) {
        return NULL;
    }
    address = (void *)(uintptr_t)value;
    if ((uintptr_t)address < PYGL_SLOT_MIN_REAL) {
        if (pygl_current->handle != NULL) {
            pygl_current->slots[command->slot] = (void *)PYGL_SLOT_ABSENT;
        }
        PyErr_Format(pygl_null_function_error,
                     "Attempt to call an undefined function %s, check for bool(%s) "
                     "before calling",
                     command->name, command->name);
        return NULL;
    }
    pygl_current->slots[command->slot] = address;
    return address;
}

/* Every call verifies that a context is current.  Reached only when
 * OpenGL.CONTEXT_CHECKING is on, which is why it can afford to ask. */
void *pygl_slot_checked(GLProc *self)
{
    void *fp;
    /* The raw platform address, not the Python one: this runs per call. */
    pygl_sync_context_fast();
    if (pygl_current->is_null_context && pygl_needs_context(self->info)) {
        PyErr_Format(pygl_no_context_error,
                     "Attempt to call %s with no current OpenGL context",
                     self->info->name);
        return NULL;
    }
    fp = pygl_current->slots[self->info->slot];
    if ((uintptr_t)fp >= PYGL_SLOT_MIN_REAL) {
        return fp;
    }
    return pygl_slot_slow(self);
}

/* ------------------------------------------------------------------ *
 * errors
 * ------------------------------------------------------------------ */

PyObject *pygl_arity_error(GLProc *self, Py_ssize_t want, Py_ssize_t got)
{
    PyErr_Format(PyExc_TypeError, "%s takes exactly %zd arguments (%zd given)",
                 self->info->name, want, got);
    return NULL;
}

PyObject *pygl_arity_range_error(GLProc *self, Py_ssize_t low, Py_ssize_t high,
                                 Py_ssize_t got)
{
    PyErr_Format(PyExc_TypeError,
                 "%s takes from %zd to %zd arguments (%zd given)", self->info->name,
                 low, high, got);
    return NULL;
}

/* Bad scalar arguments raise ctypes.ArgumentError today.  Compatibility is the
 * point of the exercise, so the C stub raises the same type; the message text
 * is deliberately not part of the contract. */
void pygl_argument_error(GLProc *self, Py_ssize_t index, const char *expected)
{
    PyErr_Format(pygl_ctypes_argument_error, "argument %zd: %s: expected %s",
                 index + 1, "TypeError", expected);
}

/* GL_DEBUG_TYPE_ERROR.  Declared here rather than included so that the runtime
 * depends on no GL header. */
#define PYGL_DEBUG_TYPE_ERROR 0x824C

/* Called by the driver, on the calling thread, during the GL call.  It must do
 * as little as possible: no Python objects, no allocation.  Copying the text
 * and setting a flag is all that is needed, because the stub reads the flag
 * immediately afterwards. */
static void
#if defined(_WIN32)
    __stdcall
#endif
    pygl_debug_callback(unsigned int source, unsigned int type, unsigned int id,
                        unsigned int severity, int length, const char *message,
                        const void *user)
{
    size_t limit;
    (void)source;
    (void)severity;
    (void)user;
    if (type != PYGL_DEBUG_TYPE_ERROR || pygl_error_suspended) {
        return;
    }
    limit = (size_t)(length < 0 ? 0 : length);
    if (limit == 0 && message != NULL) {
        limit = strlen(message);
    }
    if (limit >= PYGL_DEBUG_MESSAGE_MAX) {
        limit = PYGL_DEBUG_MESSAGE_MAX - 1;
    }
    if (message != NULL && limit) {
        memcpy(pygl_debug_message, message, limit);
    }
    pygl_debug_message[limit] = '\0';
    pygl_debug_id = id;
    pygl_debug_pending = 1;
}

int pygl_check_error(GLProc *self)
{
    void *fp;
    unsigned int code;
    PyObject *result;

    if (pygl_error_suspended) {
        return 0;
    }
    if (pygl_error_mode == PYGL_ERRORS_DEBUG) {
        if (!pygl_debug_pending) {
            return 0;
        }
        pygl_debug_pending = 0;
        result = PyObject_CallMethod(pygl_support, "raise_debug_error", "Iss",
                                     pygl_debug_id, pygl_debug_message,
                                     self->info->name);
        Py_XDECREF(result);
        return -1;
    }
    if (pygl_error_slot < 0) {
        return 0;
    }
    fp = pygl_current->slots[pygl_error_slot];
    if ((uintptr_t)fp < PYGL_SLOT_MIN_REAL) {
        /* This context has not resolved glGetError yet. */
        if (pygl_error_proc == NULL) {
            return 0;
        }
        fp = pygl_slot((GLProc *)pygl_error_proc);
        if (fp == NULL) {
            PyErr_Clear();
            return 0;
        }
    }
    code = ((unsigned int (*)(void))fp)();
    if (code == 0) {
        return 0;
    }
    result = PyObject_CallMethod(pygl_support, "raise_gl_error", "Is",
                                 code, self->info->name);
    Py_XDECREF(result);
    return -1;
}

int pygl_boolean_slow(PyObject *object)
{
    int result = PyObject_IsTrue(object);
    return result < 0 ? 0 : result;
}

/* The address of whatever ArrayDatatype calls a data pointer.  It is usually
 * an integer, but the ctypes handlers answer with a byref result, which
 * carries its address rather than stating it. */
static int pygl_address_of(PyObject *object, void **out)
{
    unsigned long long value = PyLong_AsUnsignedLongLong(object);
    if (!PyErr_Occurred()) {
        *out = (void *)(uintptr_t)value;
        return 0;
    }
    PyErr_Clear();
    {
        PyObject *number = PyObject_CallMethod(pygl_support, "as_pointer", "O",
                                               object);
        if (number == NULL) {
            return -1;
        }
        value = PyLong_AsUnsignedLongLong(number);
        Py_DECREF(number);
        if (PyErr_Occurred()) {
            return -1;
        }
    }
    *out = (void *)(uintptr_t)value;
    return 0;
}

void *pygl_pointer_slow(PyObject *object)
{
    unsigned long long value;
    PyObject *number;
    if (PyLong_Check(object)) {
        return (void *)(uintptr_t)PyLong_AsUnsignedLongLongMask(object);
    }
    /* ctypes objects, opaque pointer instances and anything else that can
     * produce an address go through the support layer, which knows about the
     * whole set. */
    number = PyObject_CallMethod(pygl_support, "as_pointer", "O", object);
    if (number == NULL) {
        return NULL;
    }
    value = PyLong_AsUnsignedLongLong(number);
    Py_DECREF(number);
    return (void *)(uintptr_t)value;
}

/* ------------------------------------------------------------------ *
 * arrays
 *
 * The rule, from the plan: the fast path may accelerate, never reject.  An
 * exact format match is used directly; everything else falls through to
 * ArrayDatatype, which behaves exactly as it does today.  A mismatch is a
 * cheap branch, not an error.
 * ------------------------------------------------------------------ */

static int pygl_format_matches(const PyGLElement *element, const char *format)
{
    char code;
    if (element->primary == '\0') {
        return 0;
    }
    if (element->primary == '*') {
        return 1;
    }
    if (format == NULL) {
        /* An exporter with no format is bytes-like; accept it only where the
         * element is byte-sized, matching what ArrayDatatype would do. */
        return element->itemsize == 1;
    }
    code = format[0];
    if (code == '<' || code == '=' || code == '@' || code == '|') {
        code = format[1];
        if (code == '\0' || format[2] != '\0') {
            return 0;
        }
    } else if (format[1] != '\0') {
        return 0;
    }
    return code == element->primary || (element->alt1 && code == element->alt1) ||
           (element->alt2 && code == element->alt2);
}

/* A ctypes scalar or pointer exports a buffer over its own storage, which is
 * not what it means as a GL argument. */
static int pygl_is_ctypes_pointer(PyObject *object)
{
    if (pygl_ctypes_simple != NULL &&
        PyObject_TypeCheck(object, (PyTypeObject *)pygl_ctypes_simple)) {
        return 1;
    }
    if (pygl_ctypes_pointer != NULL &&
        PyObject_TypeCheck(object, (PyTypeObject *)pygl_ctypes_pointer)) {
        return 1;
    }
    return 0;
}

static PyObject *pygl_array_type(const PyGLElement *element)
{
    PyObject *type = PyList_GetItem(pygl_array_types, element->array_index);
    if (type == NULL) {
        PyErr_Format(PyExc_RuntimeError, "no array type registered for %s",
                     element->name);
    }
    return type;
}

/* The fall-through: hand the object to ArrayDatatype exactly as wrapper.py
 * does, keep what comes back alive for the duration of the call, and take the
 * data pointer from it.  This is what makes VBO offsets, ctypes objects,
 * lists, and third-party FormatHandler registrations all keep working. */
static int pygl_array_convert(PyObject *object, const PyGLElement *element,
                              PyGLBuf *out)
{
    PyObject *type, *converted, *pointer;
    void *address;

    type = pygl_array_type(element);
    if (type == NULL) {
        return -1;
    }
    converted = PyObject_CallMethodOneArg(type, pygl_str_asArray, object);
    if (converted == NULL) {
        return -1;
    }
    pointer = PyObject_CallMethodOneArg(type, pygl_str_dataPointer, converted);
    if (pointer == NULL) {
        Py_DECREF(converted);
        return -1;
    }
    if (pygl_address_of(pointer, &address) < 0) {
        Py_DECREF(pointer);
        Py_DECREF(converted);
        return -1;
    }
    Py_DECREF(pointer);
    out->owner = converted;
    out->have_view = 0;
    out->pointer = address;
    return 0;
}

/* `writable` is set for output parameters, where the GL writes into the
 * caller's memory.  A read-only exporter -- a numpy scalar, a bytes object --
 * then fails the request and falls through to the conversion path, which
 * allocates, exactly as the ctypes layer does today. */
static int pygl_array_acquire(PyObject *object, const PyGLElement *element,
                              PyGLBuf *out, int writable)
{
    int flags = PyBUF_C_CONTIGUOUS | PyBUF_FORMAT;
    out->owner = NULL;
    out->have_view = 0;
    out->pointer = NULL;

    if (object == NULL || object == Py_None) {
        /* None is a null pointer, which is meaningful for a great many entry
         * points -- a VBO offset of zero, an unbound client array. */
        return 0;
    }
    if (writable) {
        flags |= PyBUF_WRITABLE;
    }
    if (pygl_is_ctypes_pointer(object)) {
        if (element->primary == '*') {
            /* A void * parameter wants the address the ctypes object holds,
             * which is what the ctypes layer passes.  ArrayDatatype cannot
             * answer for the opaque pointer classes. */
            void *address = pygl_pointer_slow(object);
            if (address == NULL && PyErr_Occurred()) {
                return -1;
            }
            out->owner = Py_NewRef(object);
            out->pointer = address;
            return 0;
        }
    } else if (PyObject_CheckBuffer(object)) {
        if (PyObject_GetBuffer(object, &out->view, flags) == 0) {
            if (pygl_format_matches(element, out->view.format)) {
                out->have_view = 1;
                out->pointer = out->view.buf;
                /* The frame holds the object itself, so an output parameter
                 * the caller supplied is what gets handed back. */
                out->owner = Py_NewRef(object);
                return 0;
            }
            PyBuffer_Release(&out->view);
        } else {
            PyErr_Clear();
        }
    }
    return pygl_array_convert(object, element, out);
}

int pygl_array_in(GLProc *self, PyObject *object, const PyGLElement *element,
                  Py_ssize_t index, PyGLBuf *out)
{
    (void)self;
    (void)index;
    return pygl_array_acquire(object, element, out, 0);
}

int pygl_array_in_sized(GLProc *self, PyObject *object, const PyGLElement *element,
                        Py_ssize_t index, Py_ssize_t expected, PyGLBuf *out)
{
    Py_ssize_t count;
    if (pygl_array_in(self, object, element, index, out) < 0) {
        return -1;
    }
    if (out->owner == NULL && !out->have_view) {
        /* The argument was None, which is a null pointer rather than an array
         * of the wrong length.  A zero-length sequence is *not* this case: it
         * converts to an empty array whose data pointer is also null, and
         * skipping the check for it would hand the driver address zero to read
         * from. */
        return 0;
    }
    if (!pygl_array_size_checking) {
        return 0;
    }
    if (element->itemsize == 0) {
        /* A void * parameter has no element width, so there is nothing to
         * check the caller's length against. */
        return 0;
    }
    if (out->have_view) {
        count = out->view.len;
    } else {
        PyObject *size = PyObject_CallMethod(pygl_array_type(element),
                                             "arrayByteCount", "O", out->owner);
        if (size == NULL) {
            PyErr_Clear();
            return 0;
        }
        count = PyLong_AsSsize_t(size);
        Py_DECREF(size);
        if (count < 0) {
            PyErr_Clear();
            return 0;
        }
    }
    /* The check is on the byte count and it is exact, which is what
     * arrayhelpers.asArrayTypeSize asserts today: an array of the wrong length
     * in either direction is a caller error, not something to truncate. */
    expected *= element->itemsize;
    if (count != expected) {
        PyErr_Format(PyExc_ValueError,
                     "Expected %zd byte array, got %zd byte array",
                     expected, count);
        pygl_release(out);
        return -1;
    }
    return 0;
}

static PyObject *type_or_null(const PyGLElement *element)
{
    PyObject *type = pygl_array_type(element);
    if (type == NULL) {
        PyErr_Clear();
    }
    return type;
}

/* Whether converting `original` to `converted` lost bytes. */
static int pygl_copy_shrank(PyObject *type, PyObject *original, PyObject *converted)
{
    PyObject *before, *after;
    Py_ssize_t a, b;
    if (type == NULL) {
        return 0;
    }
    before = PyObject_CallMethod(type, "arrayByteCount", "O", original);
    if (before == NULL) {
        PyErr_Clear();
        return 0;
    }
    after = PyObject_CallMethod(type, "arrayByteCount", "O", converted);
    if (after == NULL) {
        PyErr_Clear();
        Py_DECREF(before);
        return 0;
    }
    a = PyLong_AsSsize_t(before);
    b = PyLong_AsSsize_t(after);
    Py_DECREF(before);
    Py_DECREF(after);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return 0;
    }
    return b < a;
}

int pygl_array_out(GLProc *self, PyObject *object, const PyGLElement *element,
                   Py_ssize_t index, Py_ssize_t count, PyGLBuf *out)
{
    PyObject *type, *allocated, *pointer;
    void *address;

    /* orPassIn is the normal path, not an exception: a caller-supplied array
     * is written into and handed back. */
    (void)index;
    if (object != NULL && object != Py_None) {
        if (pygl_array_acquire(object, element, out, 1) < 0) {
            return -1;
        }
        /* When the caller's array had to be copied to match, the GL writes
         * into the copy.  If that copy is smaller than what the caller passed,
         * the result never reaches them -- the silent "returns zeroes" bug --
         * so refuse it and say what to pass instead. */
        if (out->owner != NULL && out->owner != object &&
            pygl_copy_shrank(type_or_null(element), object, out->owner)) {
            PyErr_Format(PyExc_TypeError,
                         "%s: pass-in output array was coerced to a smaller "
                         "buffer, so the GL result cannot be written back into "
                         "your array. Pass a correctly-typed array, or None to "
                         "have one allocated.",
                         self->info->name);
            pygl_release(out);
            return -1;
        }
        return 0;
    }
    (void)self;

    out->owner = NULL;
    out->have_view = 0;
    out->pointer = NULL;

    if (element->itemsize == 0) {
        /* Nothing here knows how wide an element is, so an allocation would be
         * a guess and the GL would write past the end of it.  The generator is
         * not supposed to emit such an output; say so rather than crash. */
        PyErr_Format(PyExc_RuntimeError,
                     "%s: cannot allocate an output array of %s, which has no "
                     "element width",
                     self->info->name, element->name);
        return -1;
    }
    type = pygl_array_type(element);
    if (type == NULL) {
        return -1;
    }
    allocated = PyObject_CallMethod(type, "zeros", "(n)", count);
    if (allocated == NULL) {
        return -1;
    }
    pointer = PyObject_CallMethodOneArg(type, pygl_str_dataPointer, allocated);
    if (pointer == NULL) {
        Py_DECREF(allocated);
        return -1;
    }
    if (pygl_address_of(pointer, &address) < 0) {
        Py_DECREF(pointer);
        Py_DECREF(allocated);
        return -1;
    }
    Py_DECREF(pointer);
    out->owner = allocated;
    out->pointer = address;
    return 0;
}

/* Bisect the pname table.  It is sorted by the generator, and the search is
 * over about 1,800 entries, so this is eleven comparisons. */
static const PyGLGetSize *pygl_glget_find(const PyGLGetSize *table,
                                          Py_ssize_t count, unsigned int pname)
{
    Py_ssize_t low = 0, high = count - 1;
    while (low <= high) {
        Py_ssize_t middle = (low + high) / 2;
        if (table[middle].pname == pname) {
            return &table[middle];
        }
        if (table[middle].pname < pname) {
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }
    return NULL;
}

int pygl_array_out_glget(GLProc *self, PyObject *object, const PyGLElement *element,
                         Py_ssize_t index, unsigned int pname,
                         const PyGLGetSize *table, Py_ssize_t table_count,
                         PyGLBuf *out, Py_ssize_t *count)
{
    const PyGLGetSize *entry = pygl_glget_find(table, table_count, pname);
    PyObject *type, *allocated, *pointer, *shape;
    void *address;

    /* A caller-supplied array is taken without consulting the table, which is
     * what the ctypes converter does: the size is needed to *allocate*, not to
     * accept.  A pname the table does not know is therefore usable so long as
     * the caller brings their own array -- and several NVIDIA and EXT queries
     * are used exactly that way. */
    if (object != NULL && object != Py_None) {
        *count = (entry == NULL || entry->lookup)
                     ? 0
                     : (Py_ssize_t)entry->dim0 * (entry->dim1 ? entry->dim1 : 1);
        return pygl_array_out(self, object, element, index, *count, out);
    }

    if (entry == NULL) {
        PyErr_Format(PyExc_KeyError, "Unknown specifier 0x%04X", pname);
        return -1;
    }

    out->owner = NULL;
    out->have_view = 0;
    out->pointer = NULL;

    if (entry->lookup) {
        /* The size itself comes from a runtime query.  Six pnames in the
         * desktop table do this, so a Python call is the right cost. */
        PyObject *size = PyObject_CallMethod(pygl_support, "lookup_int", "I",
                                             entry->lookup);
        if (size == NULL) {
            return -1;
        }
        *count = PyLong_AsSsize_t(size);
        Py_DECREF(size);
        if (PyErr_Occurred()) {
            return -1;
        }
        shape = Py_BuildValue("(n)", *count);
    } else if (entry->dim1) {
        /* A matrix pname hands back a matrix, not a flat run of numbers. */
        *count = (Py_ssize_t)entry->dim0 * entry->dim1;
        shape = Py_BuildValue("(ii)", (int)entry->dim0, (int)entry->dim1);
    } else {
        *count = entry->dim0;
        shape = Py_BuildValue("(i)", (int)entry->dim0);
    }
    if (shape == NULL) {
        return -1;
    }
    type = pygl_array_type(element);
    if (type == NULL) {
        Py_DECREF(shape);
        return -1;
    }
    allocated = PyObject_CallMethodOneArg(type, pygl_str_zeros, shape);
    Py_DECREF(shape);
    if (allocated == NULL) {
        return -1;
    }
    pointer = PyObject_CallMethodOneArg(type, pygl_str_dataPointer, allocated);
    if (pointer == NULL) {
        Py_DECREF(allocated);
        return -1;
    }
    if (pygl_address_of(pointer, &address) < 0) {
        Py_DECREF(pointer);
        Py_DECREF(allocated);
        return -1;
    }
    Py_DECREF(pointer);
    out->owner = allocated;
    out->pointer = address;
    return 0;
}

/* Hand the sizing to OpenGL.images, which owns the tables and the
 * glPixelStorei setup, and keep whatever it answers with alive for the call. */
static int pygl_image(GLProc *self, const char *method, PyObject *object,
                      unsigned int format, unsigned int type, int rank, int d0,
                      int d1, int d2, PyGLBuf *out)
{
    PyObject *converted, *pointer;
    void *address;

    out->owner = NULL;
    out->have_view = 0;
    out->pointer = NULL;

    converted = PyObject_CallMethod(pygl_support, method, "sIIiiiiO",
                                    self->info->name, format, type, rank, d0, d1,
                                    d2, object ? object : Py_None);
    if (converted == NULL) {
        return -1;
    }
    if (converted == Py_None) {
        /* A null image is meaningful: glTexImage2D with no pixels allocates
         * storage without initialising it. */
        Py_DECREF(converted);
        return 0;
    }
    pointer = PyObject_CallMethod(pygl_support, "image_pointer", "O", converted);
    if (pointer == NULL) {
        Py_DECREF(converted);
        return -1;
    }
    if (pygl_address_of(pointer, &address) < 0) {
        Py_DECREF(pointer);
        Py_DECREF(converted);
        return -1;
    }
    Py_DECREF(pointer);
    out->owner = converted;
    out->pointer = address;
    return 0;
}

int pygl_image_in(GLProc *self, PyObject *object, unsigned int format,
                  unsigned int type, int rank, int d0, int d1, int d2,
                  PyGLBuf *out)
{
    return pygl_image(self, "image_input", object, format, type, rank, d0, d1,
                      d2, out);
}

int pygl_image_out(GLProc *self, PyObject *object, unsigned int format,
                   unsigned int type, int rank, int d0, int d1, int d2,
                   PyGLBuf *out)
{
    return pygl_image(self, "image_output", object, format, type, rank, d0, d1,
                      d2, out);
}

/* What a read hands back.  UNSIGNED_BYTE_IMAGES_AS_STRING turns an unsigned
 * byte image into bytes, which is what it does today. */
PyObject *pygl_image_value(PyGLBuf *buffer, unsigned int type)
{
    if (buffer->owner == NULL) {
        Py_RETURN_NONE;
    }
    return PyObject_CallMethod(pygl_support, "image_result", "OI", buffer->owner,
                               type);
}

void pygl_release(PyGLBuf *buffer)
{
    if (buffer->have_view) {
        PyBuffer_Release(&buffer->view);
        buffer->have_view = 0;
    }
    Py_CLEAR(buffer->owner);
    buffer->pointer = NULL;
}

/* The value an output parameter contributes to the return.  A one-element
 * result is unpacked to a scalar, which is what the friendly API does today. */
PyObject *pygl_output_value(PyGLBuf *buffer, const PyGLElement *element,
                            Py_ssize_t count)
{
    PyObject *value = buffer->owner;
    if (value == NULL) {
        Py_RETURN_NONE;
    }
    if (count == 1 && pygl_size_1_array_unpack) {
        PyObject *item = PySequence_GetItem(value, 0);
        if (item == NULL) {
            PyErr_Clear();
            Py_INCREF(value);
            return value;
        }
        return item;
    }
    (void)element;
    Py_INCREF(value);
    return value;
}

PyObject *pygl_output_tuple(PyGLBuf *buffers, const PyGLOutput *outputs,
                            Py_ssize_t count)
{
    PyObject *result = PyTuple_New(count);
    Py_ssize_t index;
    if (result == NULL) {
        return NULL;
    }
    for (index = 0; index < count; index++) {
        const PyGLOutput *output = &outputs[index];
        PyObject *value = pygl_output_value(&buffers[output->slot],
                                            output->element, output->count);
        if (value == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        PyTuple_SET_ITEM(result, index, value);
    }
    return result;
}

PyObject *pygl_bytes_or_none(const char *value)
{
    if (value == NULL) {
        Py_RETURN_NONE;
    }
    return PyBytes_FromString(value);
}

/* A mapped-buffer pointer is handed back as the address itself, which is what
 * a ctypes c_void_p restype produces: an int, or None for a null pointer. */
PyObject *pygl_address_or_none(void *value)
{
    if (value == NULL) {
        Py_RETURN_NONE;
    }
    return PyLong_FromVoidPtr(value);
}

PyObject *pygl_opaque(void *value, const char *type_name)
{
    if (value == NULL) {
        Py_RETURN_NONE;
    }
    return PyObject_CallMethod(pygl_support, "opaque", "Ks",
                               (unsigned long long)(uintptr_t)value, type_name);
}

/* ------------------------------------------------------------------ *
 * the GLProc callable
 * ------------------------------------------------------------------ */

static void GLProc_dealloc(GLProc *self)
{
    if (self->weakreflist != NULL) {
        PyObject_ClearWeakRefs((PyObject *)self);
    }
    Py_XDECREF(self->ctypes_callable);
    Py_XDECREF(self->errcheck);
    Py_XDECREF(self->doc_override);
    Py_XDECREF(self->extension_override);
    Py_XDECREF(self->dict);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *GLProc_repr(GLProc *self)
{
    return PyUnicode_FromFormat("<OpenGL entry point %s>", self->info->name);
}

/* bool(glFoo) answers for the current context.  Today it resolves once and
 * caches for the process, so the same expression could not answer True in a
 * context that has the extension and False in one that does not. */
static int GLProc_bool(GLProc *self)
{
    void *fp;
    pygl_sync_context();
    fp = pygl_current->slots[self->info->slot];
    if ((uintptr_t)fp >= PYGL_SLOT_MIN_REAL) {
        return 1;
    }
    if (fp == (void *)PYGL_SLOT_ABSENT) {
        return 0;
    }
    fp = pygl_slot_slow(self);
    if (fp == NULL) {
        PyErr_Clear();
        return 0;
    }
    return 1;
}

static PyNumberMethods GLProc_as_number = {
    .nb_bool = (inquiry)GLProc_bool,
};

static PyObject *GLProc_get_name(GLProc *self, void *closure)
{
    (void)closure;
    return PyUnicode_FromString(self->info->name);
}

static PyObject *GLProc_get_doc(GLProc *self, void *closure)
{
    (void)closure;
    if (self->doc_override != NULL) {
        return Py_NewRef(self->doc_override);
    }
    if (self->info->doc == NULL) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(self->info->doc);
}

/* The generated docstring is a default, not a fact about the entry point:
 * OpenGL.GL.glget replaces several with hand-written prose, and clients may
 * do the same. */
static int GLProc_set_doc(GLProc *self, PyObject *value, void *closure)
{
    (void)closure;
    Py_XSETREF(self->doc_override, Py_XNewRef(value));
    return 0;
}

static PyObject *GLProc_get_text_signature(GLProc *self, void *closure)
{
    (void)closure;
    if (self->info->text_signature == NULL) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(self->info->text_signature);
}

/* inspect.signature() only reads __text_signature__ from the builtin callable
 * types, so an entry point answers with a Signature it builds from the same
 * string.  It is built on demand: nothing on the call path reads it. */
static PyObject *GLProc_get_signature(GLProc *self, void *closure)
{
    (void)closure;
    if (self->info->text_signature == NULL) {
        PyErr_SetString(PyExc_AttributeError, "__signature__");
        return NULL;
    }
    return PyObject_CallMethod(pygl_support, "signature_for", "ss",
                               self->info->name, self->info->text_signature);
}

static PyObject *GLProc_get_arg_names(GLProc *self, void *closure)
{
    Py_ssize_t index;
    PyObject *result;
    (void)closure;
    result = PyList_New(self->info->arg_count);
    if (result == NULL) {
        return NULL;
    }
    for (index = 0; index < self->info->arg_count; index++) {
        PyObject *name = PyUnicode_FromString(self->info->arg_names[index]);
        if (name == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, index, name);
    }
    return result;
}

static PyObject *GLProc_get_extension(GLProc *self, void *closure)
{
    (void)closure;
    if (self->has_extension_override) {
        return Py_NewRef(self->extension_override ? self->extension_override
                                                  : Py_None);
    }
    if (self->info->extension == NULL || self->info->extension[0] == '\0') {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(self->info->extension);
}

/* Assigning `extension` says which extension to check before resolving, and
 * None says to resolve as core.  It has to take effect before the entry point
 * is first called, which is how the friendly modules use it. */
static int GLProc_set_extension(GLProc *self, PyObject *value, void *closure)
{
    (void)closure;
    Py_XSETREF(self->extension_override,
               (value == NULL || value == Py_None) ? NULL : Py_NewRef(value));
    self->has_extension_override = 1;
    return 0;
}

static PyObject *GLProc_get_deprecated(GLProc *self, void *closure)
{
    (void)closure;
    return PyBool_FromLong(self->info->deprecated);
}

static PyObject *GLProc_get_module(GLProc *self, void *closure)
{
    (void)closure;
    return PyObject_CallMethod(pygl_support, "module_for", "s", self->info->name);
}

/* argtypes, restype and DLL come from the ctypes binding, which clients read
 * and wrapper.py needs.  Built on demand: nothing on the call path uses them. */
static PyObject *GLProc_ctypes_attribute(GLProc *self, const char *attribute)
{
    PyObject *callable = PyObject_CallMethod(pygl_support, "ctypes_callable", "s",
                                             self->info->name);
    PyObject *result;
    if (callable == NULL) {
        return NULL;
    }
    result = PyObject_GetAttrString(callable, attribute);
    Py_DECREF(callable);
    return result;
}

static PyObject *GLProc_get_argtypes(GLProc *self, void *closure)
{
    (void)closure;
    return GLProc_ctypes_attribute(self, "argtypes");
}

static PyObject *GLProc_get_restype(GLProc *self, void *closure)
{
    (void)closure;
    return GLProc_ctypes_attribute(self, "restype");
}

static int GLProc_demote(GLProc *self);

/* Assigning the conversion the stub already performs changes nothing, so it is
 * accepted as it stands.  Asking for a different one demotes this entry point
 * to ctypes, where an arbitrary restype means what it has always meant. */
static int GLProc_set_restype(GLProc *self, PyObject *value, void *closure)
{
    PyObject *matches;
    int same;
    (void)closure;
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "cannot delete restype");
        return -1;
    }
    matches = PyObject_CallMethod(pygl_support, "restype_matches", "iO",
                                  (int)self->info->return_kind, value);
    if (matches == NULL) {
        return -1;
    }
    same = PyObject_IsTrue(matches);
    Py_DECREF(matches);
    if (same < 0) {
        return -1;
    }
    if (same) {
        return 0;
    }
    if (GLProc_demote(self) < 0) {
        return -1;
    }
    return PyObject_SetAttrString(self->ctypes_callable, "restype", value);
}

static PyObject *GLProc_get_dll(GLProc *self, void *closure)
{
    (void)closure;
    return GLProc_ctypes_attribute(self, "DLL");
}

/* Assigning errcheck or argtypes demotes this entry point to the ctypes path
 * for the life of the process.  It keeps a genuinely used debugging affordance
 * working without putting a settable callback in the hot path. */
static PyObject *pygl_demoted_call(GLProc *self, PyObject *const *args,
                                   size_t nargsf, PyObject *kwnames);

static int GLProc_demote(GLProc *self)
{
    PyObject *callable;
    if (self->ctypes_callable != NULL) {
        return 0;
    }
    callable = PyObject_CallMethod(pygl_support, "ctypes_callable", "s",
                                   self->info->name);
    if (callable == NULL) {
        return -1;
    }
    self->ctypes_callable = callable;
    self->vectorcall = (vectorcallfunc)pygl_demoted_call;
    return 0;
}

static PyObject *GLProc_get_errcheck(GLProc *self, void *closure)
{
    (void)closure;
    if (self->errcheck == NULL) {
        Py_RETURN_NONE;
    }
    Py_INCREF(self->errcheck);
    return self->errcheck;
}

static int GLProc_set_errcheck(GLProc *self, PyObject *value, void *closure)
{
    (void)closure;
    if (GLProc_demote(self) < 0) {
        return -1;
    }
    if (PyObject_SetAttrString(self->ctypes_callable, "errcheck",
                               value ? value : Py_None) < 0) {
        return -1;
    }
    Py_XSETREF(self->errcheck, Py_XNewRef(value));
    return 0;
}

static int GLProc_set_argtypes(GLProc *self, PyObject *value, void *closure)
{
    (void)closure;
    if (GLProc_demote(self) < 0) {
        return -1;
    }
    return PyObject_SetAttrString(self->ctypes_callable, "argtypes", value);
}

static PyObject *pygl_demoted_call(GLProc *self, PyObject *const *args,
                                   size_t nargsf, PyObject *kwnames)
{
    return PyObject_Vectorcall(self->ctypes_callable, args, nargsf, kwnames);
}

/* The friendly modules restate each entry point's customisations as a chain of
 * setter calls.  Where the C already implements what the call describes, the
 * call is a no-op returning the entry point itself, so the chain still ends in
 * the GLProc that the module binds.
 *
 * Where it describes something the C does not implement, correctness comes
 * before speed: the call falls back to wrapper.wrapper over the ctypes
 * binding, and that one entry point runs the way it does today. */
static PyObject *GLProc_declarative(GLProc *self, PyObject *args, PyObject *kwds)
{
    (void)args;
    (void)kwds;
    return Py_NewRef((PyObject *)self);
}

static PyObject *GLProc_fallback(GLProc *self, PyObject *args, PyObject *kwds,
                                 const char *method)
{
    PyObject *keywords, *result;

    if (self->info->hand_written) {
        /* A hand-written entry point already implements what the call
         * describes, so restating it changes nothing. */
        return Py_NewRef((PyObject *)self);
    }
    keywords = kwds ? kwds : PyDict_New();
    if (keywords == NULL) {
        return NULL;
    }
    result = PyObject_CallMethod(pygl_support, "demote_and_call", "OsOO", self,
                                 method, args, keywords);
    if (kwds == NULL) {
        Py_DECREF(keywords);
    }
    return result;
}

#define PYGL_FALLBACK_METHOD(name)                                             \
    static PyObject *GLProc_##name(GLProc *self, PyObject *args, PyObject *kwds) \
    {                                                                          \
        return GLProc_fallback(self, args, kwds, #name);                       \
    }

PYGL_FALLBACK_METHOD(setPyConverter)
PYGL_FALLBACK_METHOD(setCConverter)
PYGL_FALLBACK_METHOD(setCResolver)
PYGL_FALLBACK_METHOD(setStoreValues)
PYGL_FALLBACK_METHOD(setReturnValues)
PYGL_FALLBACK_METHOD(setImageInput)
PYGL_FALLBACK_METHOD(setDimensionsAsInts)

#define PYGL_METHOD(name, function, doc)                                       \
    {                                                                          \
        name, (PyCFunction)(void (*)(void))function, METH_VARARGS | METH_KEYWORDS, \
            doc                                                                \
    }

static PyMethodDef GLProc_methods[] = {
    PYGL_METHOD("setOutput", GLProc_declarative,
                "Already implemented by this entry point; returns it unchanged."),
    PYGL_METHOD("setInputArraySize", GLProc_declarative,
                "Already implemented by this entry point; returns it unchanged."),
    PYGL_METHOD("setPyConverter", GLProc_setPyConverter,
                "Demote to the ctypes wrapper and apply the converter there."),
    PYGL_METHOD("setCConverter", GLProc_setCConverter,
                "Demote to the ctypes wrapper and apply the converter there."),
    PYGL_METHOD("setCResolver", GLProc_setCResolver,
                "Demote to the ctypes wrapper and apply the resolver there."),
    PYGL_METHOD("setStoreValues", GLProc_setStoreValues,
                "Demote to the ctypes wrapper and store there."),
    PYGL_METHOD("setReturnValues", GLProc_setReturnValues,
                "Demote to the ctypes wrapper and return from there."),
    PYGL_METHOD("setImageInput", GLProc_setImageInput,
                "Demote to the ctypes wrapper and size the image there."),
    PYGL_METHOD("setDimensionsAsInts", GLProc_setDimensionsAsInts,
                "Demote to the ctypes wrapper and coerce dimensions there."),
    {NULL}};

static PyGetSetDef GLProc_getset[] = {
    {"__name__", (getter)GLProc_get_name, NULL, NULL, NULL},
    {"__qualname__", (getter)GLProc_get_name, NULL, NULL, NULL},
    {"__doc__", (getter)GLProc_get_doc, (setter)GLProc_set_doc, NULL, NULL},
    {"__text_signature__", (getter)GLProc_get_text_signature, NULL, NULL, NULL},
    {"__signature__", (getter)GLProc_get_signature, NULL, NULL, NULL},
    {"__module__", (getter)GLProc_get_module, NULL, NULL, NULL},
    {"argNames", (getter)GLProc_get_arg_names, NULL, NULL, NULL},
    {"argtypes", (getter)GLProc_get_argtypes, (setter)GLProc_set_argtypes, NULL,
     NULL},
    {"restype", (getter)GLProc_get_restype, (setter)GLProc_set_restype, NULL,
     NULL},
    {"DLL", (getter)GLProc_get_dll, NULL, NULL, NULL},
    {"extension", (getter)GLProc_get_extension, (setter)GLProc_set_extension,
     NULL, NULL},
    {"deprecated", (getter)GLProc_get_deprecated, NULL, NULL, NULL},
    {"errcheck", (getter)GLProc_get_errcheck, (setter)GLProc_set_errcheck, NULL,
     NULL},
    {NULL}};

PyTypeObject PyGLProc_Type = {
    PyVarObject_HEAD_INIT(NULL, 0).tp_name = "OpenGL._dispatch.GLProc",
    .tp_basicsize = sizeof(GLProc),
    .tp_dealloc = (destructor)GLProc_dealloc,
    .tp_repr = (reprfunc)GLProc_repr,
    .tp_as_number = &GLProc_as_number,
    .tp_call = PyVectorcall_Call,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_VECTORCALL,
    .tp_vectorcall_offset = offsetof(GLProc, vectorcall),
    .tp_weaklistoffset = offsetof(GLProc, weakreflist),
    .tp_dictoffset = offsetof(GLProc, dict),
    .tp_getattro = PyObject_GenericGetAttr,
    .tp_setattro = PyObject_GenericSetAttr,
    .tp_methods = GLProc_methods,
    .tp_getset = GLProc_getset,
    .tp_doc = "An OpenGL entry point, dispatched through the current context's "
              "table.",
};

/* ------------------------------------------------------------------ *
 * registration
 * ------------------------------------------------------------------ */

int pygl_set_command_count(Py_ssize_t count)
{
    if (count > pygl_command_count) {
        pygl_command_count = count;
    }
    return 0;
}

PyObject *pygl_make_proc(const PyGLCommand *command, vectorcallfunc stub)
{
    GLProc *proc = PyObject_New(GLProc, &PyGLProc_Type);
    if (proc == NULL) {
        return NULL;
    }
    proc->vectorcall = stub;
    proc->info = command;
    proc->ctypes_callable = NULL;
    proc->errcheck = NULL;
    proc->weakreflist = NULL;
    proc->doc_override = NULL;
    proc->extension_override = NULL;
    proc->has_extension_override = 0;
    proc->dict = NULL;
    return (PyObject *)proc;
}

static const char *const pygl_api_names[PYGL_API_COUNT] = {
    "GL", "GLES1", "GLES2", "GLES3", "GLSC2", "GLX", "WGL", "EGL"};

int pygl_register_entries(PyObject *mapping, const PyGLEntry *entries)
{
    const PyGLEntry *entry;
    for (entry = entries; entry->info != NULL; entry++) {
        PyObject *proc, *key;
        if ((Py_ssize_t)entry->info->slot + 1 > pygl_command_count) {
            pygl_command_count = (Py_ssize_t)entry->info->slot + 1;
        }
        proc = pygl_make_proc(entry->info, entry->stub);
        if (proc == NULL) {
            return -1;
        }
        key = Py_BuildValue("(ss)", pygl_api_names[entry->info->api],
                            entry->info->name);
        if (key == NULL) {
            Py_DECREF(proc);
            return -1;
        }
        if (PyDict_SetItem(mapping, key, proc) < 0) {
            Py_DECREF(key);
            Py_DECREF(proc);
            return -1;
        }
        Py_DECREF(key);
        Py_DECREF(proc);
    }
    return 0;
}

/* ------------------------------------------------------------------ *
 * the module's own methods
 * ------------------------------------------------------------------ */

static PyObject *pygl_py_make_current(PyObject *module, PyObject *argument)
{
    unsigned long long handle;
    (void)module;
    handle = PyLong_AsUnsignedLongLong(argument);
    if (PyErr_Occurred()) {
        return NULL;
    }
    if (pygl_make_current((void *)(uintptr_t)handle) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *pygl_py_current_handle(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    return PyLong_FromUnsignedLongLong((unsigned long long)(uintptr_t)pygl_current->handle);
}

static PyObject *pygl_py_forget_context(PyObject *module, PyObject *argument)
{
    unsigned long long handle;
    PyGLDispatch *table, *previous = NULL;
    (void)module;
    handle = PyLong_AsUnsignedLongLong(argument);
    if (PyErr_Occurred()) {
        return NULL;
    }
    PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
    for (table = pygl_tables; table != NULL; previous = table, table = table->next) {
        if (table->handle == (void *)(uintptr_t)handle) {
            if (previous == NULL) {
                pygl_tables = table->next;
            } else {
                previous->next = table->next;
            }
            if (pygl_current == table) {
                pygl_current = &pygl_default_table;
            }
            pygl_table_free(table);
            break;
        }
    }
    PyThread_release_lock(pygl_tables_lock);
    Py_RETURN_NONE;
}

static PyObject *pygl_py_context_count(PyObject *module, PyObject *noargs)
{
    Py_ssize_t count = 0;
    PyGLDispatch *table;
    (void)module;
    (void)noargs;
    PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
    for (table = pygl_tables; table != NULL; table = table->next) {
        count++;
    }
    PyThread_release_lock(pygl_tables_lock);
    return PyLong_FromSsize_t(count);
}

/* Which address the current context resolved a command to, so that the
 * multi-context tests can assert two contexts hold independent tables. */
static PyObject *pygl_py_slot_address(PyObject *module, PyObject *argument)
{
    GLProc *proc;
    (void)module;
    if (!PyObject_TypeCheck(argument, &PyGLProc_Type)) {
        PyErr_SetString(PyExc_TypeError, "expected an OpenGL entry point");
        return NULL;
    }
    proc = (GLProc *)argument;
    return PyLong_FromUnsignedLongLong(
        (unsigned long long)(uintptr_t)pygl_current->slots[proc->info->slot]);
}

static PyObject *pygl_py_set_error_checking(PyObject *module, PyObject *args)
{
    PyObject *target = Py_None;
    int enable = 1;
    Py_ssize_t index;
    (void)module;
    if (!PyArg_ParseTuple(args, "p|O", &enable, &target)) {
        return NULL;
    }
    if (target == Py_None) {
        for (index = 0; index < pygl_command_count; index++) {
            if (enable) {
                pygl_current->flags[index] |= PYGL_F_CHECK_ERRORS;
            } else {
                pygl_current->flags[index] &= (uint8_t)~PYGL_F_CHECK_ERRORS;
            }
        }
    } else if (PyObject_TypeCheck(target, &PyGLProc_Type)) {
        uint16_t slot = ((GLProc *)target)->info->slot;
        if (enable) {
            pygl_current->flags[slot] |= PYGL_F_CHECK_ERRORS;
        } else {
            pygl_current->flags[slot] &= (uint8_t)~PYGL_F_CHECK_ERRORS;
        }
    } else {
        PyErr_SetString(PyExc_TypeError, "expected an OpenGL entry point or None");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *pygl_py_configure(PyObject *module, PyObject *args, PyObject *kwds)
{
    static char *keywords[] = {"support",           "array_types",
                               "ctypes_simple",     "ctypes_pointer",
                               "error_slot",        "get_current_context",
                               "strict_context",    "array_size_checking",
                               "error_checking",    "error_proc",
                               "size_1_array_unpack", "context_checking",
                               "context_tracking", NULL};
    PyObject *support = NULL, *array_types = NULL;
    PyObject *simple = NULL, *pointer = NULL, *error_proc = Py_None;
    int error_slot = -1, strict = 0, size_checking = 1, error_checking = 0;
    int unpack = 1, context_checking = 0, tracking = PYGL_TRACK_VERIFY;
    unsigned long long getter = 0;
    (void)module;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOOO|iKpppOppi", keywords, &support,
                                     &array_types, &simple, &pointer, &error_slot,
                                     &getter, &strict, &size_checking,
                                     &error_checking, &error_proc, &unpack,
                                     &context_checking, &tracking)) {
        return NULL;
    }
    pygl_context_checking = context_checking;
    pygl_context_tracking = tracking;
    pygl_array_size_checking = size_checking;
    pygl_size_1_array_unpack = unpack;
    pygl_default_flags = error_checking ? PYGL_F_CHECK_ERRORS : 0;
    Py_XSETREF(pygl_error_proc,
               error_proc == Py_None ? NULL : Py_NewRef(error_proc));
    Py_XSETREF(pygl_ctypes_simple, Py_NewRef(simple));
    Py_XSETREF(pygl_ctypes_pointer, Py_NewRef(pointer));
    Py_XSETREF(pygl_support, Py_NewRef(support));
    if (!PyList_Check(array_types)) {
        PyErr_SetString(PyExc_TypeError, "array_types must be a list");
        return NULL;
    }
    Py_XSETREF(pygl_array_types, Py_NewRef(array_types));
    pygl_error_slot = error_slot;
    pygl_get_current_context = (void *(*)(void))(uintptr_t)getter;
    pygl_strict_context = strict;
    if (pygl_default_flags) {
        Py_ssize_t index;
        PyGLDispatch *table;
        for (index = 0; index < pygl_command_count; index++) {
            pygl_null_table.flags[index] = pygl_default_flags;
            pygl_default_table.flags[index] = pygl_default_flags;
        }
        for (table = pygl_tables; table != NULL; table = table->next) {
            memset(table->flags, pygl_default_flags, (size_t)pygl_command_count);
        }
    }
    Py_RETURN_NONE;
}

static PyObject *pygl_py_suspend_error_checking(PyObject *module, PyObject *argument)
{
    int suspend = PyObject_IsTrue(argument);
    (void)module;
    if (suspend < 0) {
        return NULL;
    }
    pygl_error_suspended = suspend;
    Py_RETURN_NONE;
}

/* The address of the callback, so the Python side can hand it to
 * glDebugMessageCallback through the ordinary entry point. */
static PyObject *pygl_py_debug_callback_address(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    return PyLong_FromVoidPtr((void *)pygl_debug_callback);
}

static PyObject *pygl_py_set_error_mode(PyObject *module, PyObject *argument)
{
    long mode = PyLong_AsLong(argument);
    (void)module;
    if (PyErr_Occurred()) {
        return NULL;
    }
    pygl_error_mode = (int)mode;
    pygl_debug_pending = 0;
    Py_RETURN_NONE;
}

static PyObject *pygl_py_sync_context(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    pygl_sync_context();
    Py_RETURN_NONE;
}

/* Referenced by the strict-tracking path; kept distinct so that the
 * once-per-context path and the per-call path can differ. */
static PyObject *pygl_py_sync_context_fast(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    pygl_sync_context_fast();
    Py_RETURN_NONE;
}

static PyObject *pygl_py_command_count(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    return PyLong_FromSsize_t(pygl_command_count);
}

static PyMethodDef pygl_methods[] = {
    {"_configure", (PyCFunction)(void (*)(void))pygl_py_configure,
     METH_VARARGS | METH_KEYWORDS,
     "Install the Python support layer the C dispatch calls back into."},
    {"make_current", pygl_py_make_current, METH_O,
     "Dispatch this thread through the table for the given context handle."},
    {"current_handle", pygl_py_current_handle, METH_NOARGS,
     "The context handle this thread is currently dispatching through."},
    {"forget_context", pygl_py_forget_context, METH_O,
     "Free the dispatch table for a context that has been destroyed."},
    {"context_count", pygl_py_context_count, METH_NOARGS,
     "How many context dispatch tables are live."},
    {"slot_address", pygl_py_slot_address, METH_O,
     "The address the current context has resolved an entry point to."},
    {"set_error_checking", pygl_py_set_error_checking, METH_VARARGS,
     "Turn per-call error checking on or off, for one entry point or all."},
    {"suspend_error_checking", pygl_py_suspend_error_checking, METH_O,
     "Suspend per-call error checking, for the duration of a glBegin block."},
    {"debug_callback_address", pygl_py_debug_callback_address, METH_NOARGS,
     "The address of the GL_KHR_debug callback, for glDebugMessageCallback."},
    {"set_error_mode", pygl_py_set_error_mode, METH_O,
     "0 to check with glGetError, 1 to check the GL_KHR_debug flag."},
    {"sync_context", pygl_py_sync_context, METH_NOARGS,
     "Re-read the current context from the platform and switch tables."},
    {"sync_context_fast", pygl_py_sync_context_fast, METH_NOARGS,
     "As sync_context, through the raw platform address."},
    {"command_count", pygl_py_command_count, METH_NOARGS,
     "How many entry points the dispatch table holds a slot for."},
    {NULL}};

/* ------------------------------------------------------------------ *
 * module init
 * ------------------------------------------------------------------ */

/* Defined by the generated translation units. */
int pygl_register_generated(PyObject *mapping);

static int pygl_init_errors(void)
{
    PyObject *ctypes, *error;
    ctypes = PyImport_ImportModule("ctypes");
    if (ctypes == NULL) {
        return -1;
    }
    pygl_ctypes_argument_error = PyObject_GetAttrString(ctypes, "ArgumentError");
    Py_DECREF(ctypes);
    if (pygl_ctypes_argument_error == NULL) {
        return -1;
    }
    error = PyImport_ImportModule("OpenGL.error");
    if (error == NULL) {
        return -1;
    }
    pygl_null_function_error = PyObject_GetAttrString(error, "NullFunctionError");
    pygl_no_context_error = PyObject_GetAttrString(error, "NoContext");
    pygl_gl_error = PyObject_GetAttrString(error, "GLError");
    Py_DECREF(error);
    return (pygl_null_function_error && pygl_no_context_error && pygl_gl_error) ? 0
                                                                               : -1;
}

static struct PyModuleDef pygl_module_def = {
    PyModuleDef_HEAD_INIT,
    "OpenGL._dispatch._dispatch",
    "Registry-generated C implementation of the OpenGL entry points.",
    -1,
    pygl_methods,
};

PyMODINIT_FUNC PyInit__dispatch(void)
{
    PyObject *module, *entry_points;

    if (PyType_Ready(&PyGLProc_Type) < 0) {
        return NULL;
    }
    pygl_tables_lock = PyThread_allocate_lock();
    if (pygl_tables_lock == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    pygl_str_asArray = PyUnicode_InternFromString("asArray");
    pygl_str_dataPointer = PyUnicode_InternFromString("dataPointer");
    pygl_str_zeros = PyUnicode_InternFromString("zeros");
    if (!pygl_str_asArray || !pygl_str_dataPointer || !pygl_str_zeros) {
        return NULL;
    }
    if (pygl_init_errors() < 0) {
        return NULL;
    }
    module = PyModule_Create(&pygl_module_def);
    if (module == NULL) {
        return NULL;
    }
    Py_INCREF(&PyGLProc_Type);
    if (PyModule_AddObject(module, "GLProc", (PyObject *)&PyGLProc_Type) < 0) {
        Py_DECREF(&PyGLProc_Type);
        Py_DECREF(module);
        return NULL;
    }
    entry_points = PyDict_New();
    if (entry_points == NULL) {
        Py_DECREF(module);
        return NULL;
    }
    if (pygl_register_generated(entry_points) < 0) {
        Py_DECREF(entry_points);
        Py_DECREF(module);
        return NULL;
    }
    if (PyModule_AddObject(module, "entry_points", entry_points) < 0) {
        Py_DECREF(entry_points);
        Py_DECREF(module);
        return NULL;
    }
    /* Both static tables need the slot count the generated code declared. */
    pygl_null_table.slots = PyMem_Calloc((size_t)pygl_command_count, sizeof(void *));
    pygl_null_table.flags = PyMem_Calloc((size_t)pygl_command_count, sizeof(uint8_t));
    pygl_default_table.slots = PyMem_Calloc((size_t)pygl_command_count, sizeof(void *));
    pygl_default_table.flags = PyMem_Calloc((size_t)pygl_command_count, sizeof(uint8_t));
    if (pygl_null_table.slots == NULL || pygl_null_table.flags == NULL ||
        pygl_default_table.slots == NULL || pygl_default_table.flags == NULL) {
        Py_DECREF(module);
        return PyErr_NoMemory();
    }
    return module;
}
