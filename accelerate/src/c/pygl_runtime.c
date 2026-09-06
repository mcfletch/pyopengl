/* PyOpenGL C dispatch layer -- runtime.
 *
 * Holds the per-context dispatch tables, the GLProc callable, the array
 * marshalling helpers and the bridge back into Python for everything that is
 * not on the hot path.  The generated entry points in src/c/generated call
 * into this file through the macros in pygl.h.
 */
#include "pygl.h"
/* pygl_array_type_names: which OpenGL.arrays class each element index
 * means, so this file can fill its own table by name. */
#include "generated/pygl_elements.h"

/* ------------------------------------------------------------------ *
 * module-level state
 * ------------------------------------------------------------------ */

/* Filled at import from OpenGL._dispatch.support. */
static PyObject *pygl_support = NULL;      /* the support module */
static PyObject *pygl_array_types = NULL;  /* list, indexed by array_index */
static PyObject *pygl_ctypes_argument_error = NULL;
static PyObject *pygl_null_function_error = NULL;
static PyObject *pygl_no_context_error = NULL;
static PyObject *pygl_str_asArray = NULL;
static PyObject *pygl_str_dataPointer = NULL;
static PyObject *pygl_str_zeros = NULL;
/* ctypes._SimpleCData and ctypes._Pointer.  A c_void_p means the address it
 * holds, not the eight bytes it occupies, so these must never take the buffer
 * fast path -- ArrayDatatype is the authority on what they point at. */
static PyObject *pygl_ctypes_simple = NULL;
static PyObject *pygl_ctypes_pointer = NULL;

static Py_ssize_t pygl_command_count = 0;
/* One per API; see PyGLErrorSource.  Inactive until an API says how it is
 * asked, so an API nobody registered is not polled with another's getError. */
PyGLErrorSource pygl_error_sources[PYGL_API_COUNT];
static int pygl_array_size_checking = 1;
int pygl_context_checking = 0;
int pygl_context_tracking = PYGL_TRACK_NOTIFY;
/* OpenGL.SIZE_1_ARRAY_UNPACK: whether a one-element output is handed back as a
 * scalar rather than as an array of one. */
static int pygl_size_1_array_unpack = 1;
/* glGetError inside a glBegin/glEnd block is itself an invalid operation, so
 * error checking is suspended for the duration.  The ctypes path does this
 * through _ErrorChecker.onBegin/onEnd; this is the same switch. */
/* Thread-local: a glBegin block is a property of the thread drawing, and one
 * thread entering one must not silence error checking for another.  The
 * ctypes _ErrorChecker.onBegin has the same global behaviour, so this is
 * where the two diverge deliberately -- a rewrite is the moment to fix it
 * rather than reproduce it. */
static PYGL_THREAD_LOCAL int pygl_error_suspended = 0;

/* GL_KHR_debug reporting.  The driver calls pygl_debug_callback during the GL
 * call itself when GL_DEBUG_OUTPUT_SYNCHRONOUS is on, so the callback records
 * what happened and the stub's check becomes a read of `pygl_debug_pending`
 * rather than a glGetError round trip. */
PYGL_THREAD_LOCAL int pygl_debug_pending = 0;
#define PYGL_DEBUG_MESSAGE_MAX 1024
static PYGL_THREAD_LOCAL char pygl_debug_message[PYGL_DEBUG_MESSAGE_MAX];
static PYGL_THREAD_LOCAL unsigned int pygl_debug_id = 0;
/* The flag byte a freshly created context table starts every slot at, so that
 * OpenGL.ERROR_CHECKING means the same thing in a context created later. */
static uint8_t pygl_default_flags = 0;

/* Which API an entry point belongs to, as a name.
 *
 * glClear exists in GL and in GLES2 as separate bindings resolved from
 * separate libraries, so the name alone does not identify one.  Everything
 * the C asks the Python layer about an entry point passes this too --
 * otherwise demoting a GLES2 binding looks up the desktop GL function of the
 * same name, from the GL library, which on a system serving both is a call
 * into the wrong library. */
static const char *pygl_api_name(uint8_t api);

/* Install how one API is asked for its errors.  `proc` is that API's getError
 * entry point, kept so the check can resolve its own slot in a context that
 * has not called it yet.  An API with neither slot nor proc is not polled. */
static void pygl_install_error_source(uint8_t api, int slot, PyObject *proc,
                                      unsigned int no_error, int gl_family)
{
    PyGLErrorSource *source = &pygl_error_sources[api];
    PyObject *held = (proc == NULL || proc == Py_None) ? NULL : Py_NewRef(proc);
    Py_XSETREF(source->proc, held);
    source->slot = slot;
    source->no_error = no_error;
    source->gl_family = gl_family;
    source->active = (slot >= 0 || source->proc != NULL);
}

/* The platform's "which context is current" function, as a raw address, so the
 * strict-tracking mode does not pay a Python call.  Costs about 95ns on the
 * reference machine, which is why it is not on the default path. */
static void *(*pygl_get_current_context)(void) = NULL;

/* ------------------------------------------------------------------ *
 * per-context dispatch tables
 * ------------------------------------------------------------------ */

/* Used when the platform reports that no context is current.  Named fields,
 * because a positional initialiser has to be revisited every time the struct
 * gains one -- and the compiler only says so when the types happen to
 * disagree. */
static PyGLDispatch pygl_null_table = {.is_null_context = 1};
/* Used when the platform offers no way to ask which context is current.  It
 * behaves as an ordinary table, because "we cannot tell" must not be reported
 * as "there is none". */
static PyGLDispatch pygl_default_table = {.is_null_context = 0};
PYGL_THREAD_LOCAL PyGLDispatch *pygl_current = &pygl_default_table;

static PyGLDispatch *pygl_tables = NULL; /* handle -> table, a short list */

/* Tables whose context has been forgotten.
 *
 * They are not freed.  `pygl_current` is thread-local, so forgetting a context
 * can only clear the pointer belonging to the thread that asked: every other
 * thread that ever made that context current still points at the table, and
 * its next dispatch reads it.  Freeing here is a use-after-free in any program
 * that destroys a context from one thread while another is drawing -- which is
 * the ordinary shape of a program with a window per thread, and the
 * documentation recommends the call.
 *
 * So a forgotten table is emptied and retired instead.  Its slots read as
 * PYGL_SLOT_UNRESOLVED, which sends a stale thread down the slow path, where
 * syncing the context moves it to the right table; and its handle is cleared,
 * so it can never be found again.
 *
 * A retired table costs nine bytes per entry point -- 43 KB against the 4,859
 * commands of a current registry -- and the count is bounded by the number of
 * contexts the process ever made.  For the ordinary program that is one or two;
 * for one that opens a context per document window over a long session it
 * accumulates, so pygl_reclaim_retired() frees the lot at a moment the caller
 * declares quiescent.  Nothing frees them on its own, because nothing here can
 * see whether a thread still holds the pointer. */
static PyGLDispatch *pygl_retired = NULL;
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
    } else {
        /* Out of memory.  Returning the no-context table would answer "no
         * context is current", which is wrong rather than merely unhelpful. */
        PyErr_NoMemory();
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
    /* A table this thread is coming back to was armed for the context it
     * described when it was last used, and a handle is an address the driver
     * reuses.  So the first check after a switch asks the driver rather than
     * trusting the flag; if the callback is still this context's, the audit
     * costs one glGetError and the flag is trusted again. */
    if (table->error_mode == PYGL_ERRORS_DEBUG) {
        table->audit_countdown = 1;
    }
    return 0;
}

/* A glBegin/glEnd block belongs to the context it was opened in, so an
 * application saying it has switched or destroyed a context ends the block.
 * Without this a block that never reached its glEnd -- an exception between
 * the two -- leaves error checking off for the rest of the process, and every
 * later context inherits the silence.
 *
 * Only what the application says counts, not pygl_sync_context noticing: the
 * slow path runs *inside* the glBegin that opened the block, when the table
 * for the new context is still being built, and treating that as a switch
 * would tear down the suspension the call had just put up. */
static void pygl_end_begin_block(void)
{
    pygl_error_suspended = 0;
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
    return command->needs_context;
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
        result = PyObject_CallMethod(
            pygl_support, "resolve", "sssi", command->name, extension,
            /* An override names one extension deliberately, so it stands
             * alone; otherwise every extension that declares the command
             * counts. */
            self->has_extension_override ? "" : command->alternates,
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
    /* Only where the caller asked to be told.  This path is also reached with
     * PYOPENGL_CONTEXT_TRACKING=verify, which is an accuracy option and says
     * nothing about wanting an exception: without the flag here, selecting
     * verify would silently turn CONTEXT_CHECKING on and break the property
     * the layer relies on -- that calling with no current context is a no-op,
     * which is what a cleanup handler running after its context has gone
     * depends on. */
    if (pygl_context_checking && pygl_current->is_null_context &&
        pygl_needs_context(self->info)) {
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

/* Bad scalar arguments raise ctypes.ArgumentError.  That type is part of
 * PyOpenGL's own interface -- OpenGL.error re-exports it, and the ctypes
 * wrapper catches it to add the converted arguments -- so a program that
 * catches it has to keep working here.  The type is the contract; the message
 * is not, so whatever the conversion said is carried across rather than
 * reconstructed.
 *
 * Only a conversion failure is translated.  A MemoryError or a
 * KeyboardInterrupt that happened to land in the same window is left alone:
 * calling either of those a bad argument would be a lie, and a caller
 * catching ArgumentError would swallow it. */
void pygl_argument_error(GLProc *self)
{
    PyObject *type = NULL, *value = NULL, *traceback = NULL, *text = NULL;

    if (!PyErr_Occurred()) {
        return;
    }
    if (!PyErr_ExceptionMatches(PyExc_TypeError)
        && !PyErr_ExceptionMatches(PyExc_ValueError)
        && !PyErr_ExceptionMatches(PyExc_OverflowError)) {
        return;
    }
    PyErr_Fetch(&type, &value, &traceback);
    PyErr_NormalizeException(&type, &value, &traceback);
    if (value != NULL) {
        text = PyObject_Str(value);
    }
    if (text == NULL) {
        /* Whatever __str__ raised is discarded so that the original argument
         * error is what the caller sees.  PyErr_Restore overwrites rather than
         * chains, so clearing first is what makes that a decision. */
        PyErr_Clear();
        PyErr_Restore(type, value, traceback);
        return;
    }
    PyErr_Format(pygl_ctypes_argument_error, "%s: %U", self->info->name, text);
    Py_DECREF(text);
    Py_XDECREF(type);
    Py_XDECREF(value);
    Py_XDECREF(traceback);
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
    /* A driver may report a length with no text -- one it could not format,
     * say.  Terminating at that length rather than at zero would leave the
     * previous callback's bytes in front of the terminator, and the exception
     * would carry the previous error's message. */
    limit = (message == NULL) ? 0 : (size_t)(length < 0 ? 0 : length);
    if (limit == 0 && message != NULL) {
        limit = strlen(message);
    }
    if (limit >= PYGL_DEBUG_MESSAGE_MAX) {
        limit = PYGL_DEBUG_MESSAGE_MAX - 1;
    }
    if (limit) {
        memcpy(pygl_debug_message, message, limit);
    }
    pygl_debug_message[limit] = '\0';
    pygl_debug_id = id;
    pygl_debug_pending = 1;
}

/* The arguments the call was made with, for the exception to carry.  Clients
 * read err.pyArgs, so an error that does not know them is a poorer report
 * than the one they have today. */
static PyObject *pygl_arg_tuple(PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *tuple;
    Py_ssize_t index;
    if (args == NULL || nargs < 0) {
        Py_RETURN_NONE;
    }
    tuple = PyTuple_New(nargs);
    if (tuple == NULL) {
        PyErr_Clear();
        Py_RETURN_NONE;
    }
    for (index = 0; index < nargs; index++) {
        PyTuple_SET_ITEM(tuple, index, Py_NewRef(args[index]));
    }
    return tuple;
}

/* The code the driver has recorded, or 0.
 *
 * Both notice mechanisms want it.  GL_KHR_debug says *that* an error happened
 * and what the driver called it in prose; the code itself still comes from
 * glGetError, and it is the code that GLError.err documents and that a caller
 * branches on.  Asking costs a driver round trip, which is why it is asked only
 * once an error is known to be there. */
static unsigned int pygl_error_code(const PyGLErrorSource *source)
{
    void *fp;
    if (source->slot < 0) {
        return source->no_error;
    }
    fp = pygl_current->slots[source->slot];
    if ((uintptr_t)fp < PYGL_SLOT_MIN_REAL) {
        /* This context has not resolved this API's getError yet. */
        if (source->proc == NULL) {
            return source->no_error;
        }
        fp = pygl_slot((GLProc *)source->proc);
        if (fp == NULL) {
            PyErr_Clear();
            return source->no_error;
        }
    }
    return ((unsigned int (*)(void))fp)();
}

/* The support layer's two raisers are supposed to raise.  Returning -1 with
 * nothing set would surface much later as a SystemError about a function that
 * "returned a result with an exception set" -- or worse, be missed.  Both
 * branches guard it, through here, so the two cannot drift. */
static void pygl_ensure_raised(GLProc *self, unsigned int code)
{
    if (!PyErr_Occurred()) {
        PyErr_Format(pygl_null_function_error,
                     "%s failed with GL error 0x%X", self->info->name, code);
    }
}

int pygl_check_error(GLProc *self, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *tuple;
    unsigned int code;
    PyObject *result;
    const PyGLErrorSource *source = &pygl_error_sources[self->info->api];

    if (!source->active) {
        return 0;
    }
    /* A glBegin block suspends GL's checking, and only GL's: it is a GL
     * construct, and the ctypes path suspends the one checker it belongs to. */
    if (pygl_error_suspended && source->gl_family) {
        return 0;
    }
    if (pygl_current->error_mode == PYGL_ERRORS_DEBUG && source->gl_family) {
        if (!pygl_debug_pending) {
            /* Reached on the audit, which pygl_check_needed lets through every
             * PYGL_DEBUG_AUDIT_INTERVAL calls.  An error the driver has not
             * reported through the callback means the callback is not this
             * context's -- the handle was recycled, or something installed
             * over it -- so the context goes back to glGetError, where a check
             * cannot be silently wrong. */
            pygl_current->audit_countdown = PYGL_DEBUG_AUDIT_INTERVAL;
            code = pygl_error_code(source);
            if (code == source->no_error) {
                return 0;
            }
            pygl_current->error_mode = PYGL_ERRORS_GETERROR;
            tuple = pygl_arg_tuple(args, nargs);
            result = PyObject_CallMethod(pygl_support, "raise_gl_error", "IsOs",
                                         code, self->info->name, tuple,
                                         pygl_api_name(self->info->api));
            Py_XDECREF(tuple);
            Py_XDECREF(result);
            pygl_ensure_raised(self, code);
            return -1;
        }
        pygl_debug_pending = 0;
        code = pygl_error_code(source);
        if (code == source->no_error) {
            /* The callback fired but the queue is empty, so the error has
             * already been reported to somebody: a ctypes entry point in the
             * same context raised it through its own checker, or the caller
             * drained the queue with glGetError.  Raising here would attribute
             * a spent error to an innocent call, with err = 0 in it. */
            return 0;
        }
        tuple = pygl_arg_tuple(args, nargs);
        result = PyObject_CallMethod(pygl_support, "raise_debug_error", "IIssOs",
                                     code, pygl_debug_id, pygl_debug_message,
                                     self->info->name, tuple,
                                     pygl_api_name(self->info->api));
        Py_XDECREF(tuple);
        Py_XDECREF(result);
        pygl_ensure_raised(self, code);
        return -1;
    }
    code = pygl_error_code(source);
    if (code == source->no_error) {
        return 0;
    }
    tuple = pygl_arg_tuple(args, nargs);
    result = PyObject_CallMethod(pygl_support, "raise_gl_error", "IsOs", code,
                                 self->info->name, tuple,
                                 pygl_api_name(self->info->api));
    Py_XDECREF(tuple);
    Py_XDECREF(result);
    pygl_ensure_raised(self, code);
    return -1;
}

/* Truth of an object that is not already a Python bool.
 *
 * On failure -- an object whose truth is ambiguous, as a numpy array's is --
 * this returns 0 and *leaves the exception set*.  That is the contract, and it
 * has two halves: the pending exception survives the return, and every caller
 * checks PYGL_CONV_OK (which is PyErr_Occurred()) before using the value.
 * Clearing the error here would turn a conversion failure into a silent false;
 * a caller that reordered its checks past the conversion would do the same. */
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
        PyObject *number = PyObject_CallMethod(pygl_support, "as_pointer", "(O)",
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
    number = PyObject_CallMethod(pygl_support, "as_pointer", "(O)", object);
    if (number == NULL) {
        return NULL;
    }
    value = PyLong_AsUnsignedLongLong(number);
    if (value == (unsigned long long)-1 && PyErr_Occurred()) {
        /* Without this the caller receives (void *)-1, and its own test --
         * `address == NULL && PyErr_Occurred()` -- lets it straight through. */
        Py_DECREF(number);
        return NULL;
    }
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

/* A frame slot, before anything has been acquired into it.
 *
 * `_bufs` is an uninitialised array on the stack, so every field a later reader
 * may consult has to be written here -- `view` included.  It is only *valid*
 * where `have_view` is set, but a reader that forgets to ask reads a stale
 * stack slot rather than something obviously wrong, which is the hardest kind
 * of mistake to see: the answer differs between two identical calls. */
static void pygl_buf_reset(PyGLBuf *out)
{
    out->owner = NULL;
    out->have_view = 0;
    out->block = NULL;
    out->pointer = NULL;
    out->view.buf = NULL;
    out->view.len = 0;
}

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
    return pygl_ctypes_pointer != NULL &&
           PyObject_TypeCheck(object, (PyTypeObject *)pygl_ctypes_pointer);
}

static int pygl_is_ctypes_scalar(PyObject *object)
{
    return pygl_ctypes_simple != NULL &&
           PyObject_TypeCheck(object, (PyTypeObject *)pygl_ctypes_simple);
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

/* How many bytes of storage an acquired argument holds, or -1 where that
 * cannot be had -- a raw pointer carries no length, and neither does an object
 * ArrayDatatype declines to measure.
 *
 * "Cannot be had" is not "zero": a size check that treats the two alike either
 * refuses every raw pointer or accepts every undersized one, depending which way
 * round it reads the answer.  It is also the buffer the *driver* is handed that
 * has to be measured, not the object the caller passed: where a conversion
 * copied, the copy is what is written into and the caller's object says nothing
 * about how large it is. */
static Py_ssize_t pygl_byte_count(const PyGLElement *element, PyGLBuf *buffer)
{
    PyObject *type, *size;
    Py_ssize_t count;

    if (buffer->have_view) {
        return buffer->view.len;
    }
    /* A raw pointer is an address and nothing else -- ArrayDatatype cannot
     * measure one, and asking would only reach the same answer the long way. */
    if (buffer->owner == NULL || pygl_is_ctypes_pointer(buffer->owner)) {
        return -1;
    }
    type = pygl_array_type(element);
    if (type == NULL) {
        PyErr_Clear();
        return -1;
    }
    size = PyObject_CallMethod(type, "arrayByteCount", "(O)", buffer->owner);
    if (size == NULL) {
        PyErr_Clear();
        return -1;
    }
    count = PyLong_AsSsize_t(size);
    Py_DECREF(size);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return -1;
    }
    return count < 0 ? -1 : count;
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
    pygl_buf_reset(out);

    if (object == NULL || object == Py_None) {
        /* None is a null pointer, which is meaningful for a great many entry
         * points -- a VBO offset of zero, an unbound client array. */
        return 0;
    }
    if (writable) {
        flags |= PyBUF_WRITABLE;
    }
    if (pygl_is_ctypes_pointer(object) ||
        (pygl_is_ctypes_scalar(object) && element->primary == '*')) {
        /* A ctypes *pointer* means the address it holds, whatever the element
         * type: that is what a caller handing over a typedPointer() intends.
         *
         * A ctypes *scalar* is different, and the difference matters.  Where a
         * void * is wanted it means its value -- a c_void_p is an address.
         * Where an array is wanted it means the storage it occupies, which is
         * how GLint() serves as the output of glGetIntegerv, and reading its
         * value there would hand the driver address zero to write to. */
        void *address = pygl_pointer_slow(object);
        if (address == NULL && PyErr_Occurred()) {
            return -1;
        }
        out->owner = Py_NewRef(object);
        out->pointer = address;
        return 0;
    } else if (!pygl_is_ctypes_scalar(object) && PyObject_CheckBuffer(object)) {
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
    count = pygl_byte_count(element, out);
    if (count < 0) {
        /* Nothing here can say how long it is -- a raw pointer, or an object
         * ArrayDatatype declines to measure. */
        return 0;
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
    before = PyObject_CallMethod(type, "arrayByteCount", "(O)", original);
    if (before == NULL) {
        PyErr_Clear();
        return 0;
    }
    after = PyObject_CallMethod(type, "arrayByteCount", "(O)", converted);
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
                   Py_ssize_t index, Py_ssize_t count, int exact, PyGLBuf *out)
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
         * so refuse it and say what to pass instead.
         *
         * A copy of the *same* size -- an int32 array of four where a float32
         * array of four was wanted -- is not refused, and that is deliberate
         * rather than an oversight.  Converting and handing the copy back as
         * the return value is what orPassIn has always meant, here and in the
         * ctypes implementation, and a great deal of code passes a list or an
         * array of a convenient type and reads the result from the return
         * value.  Refusing it breaks that contract; documentation/
         * c-dispatch.html says so under "a pass-in array of the wrong type". */
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
        /* And it has to be big enough.  Without this the driver writes count
         * elements into whatever the caller supplied: glGenTextures(64, a)
         * with a four-byte array is 256 bytes into 4, which corrupts the heap
         * and is only noticed much later.  The input path has checked its
         * sizes since this layer was written; the output path is where the
         * damage is done.
         *
         * What is measured is the buffer the driver is about to be handed --
         * `out`, whatever produced it -- and not the object the caller passed.
         * Where the acquire copied, the copy is what is written into, and it is
         * sized from the caller's length rather than from `count`; a check
         * against the caller's object skips that case entirely, which is the
         * one that corrupts a PyOpenGL-allocated block rather than the
         * caller's. */
        if (exact && count > 0 && element->itemsize > 0) {
            Py_ssize_t needed = count * (Py_ssize_t)element->itemsize;
            Py_ssize_t have = pygl_byte_count(element, out);
            /* A negative answer is "nothing here can say", which a raw pointer
             * genuinely is.  It is left unchecked deliberately rather than
             * refused, and never confused with a length of zero. */
            if (have >= 0 && have < needed) {
                PyErr_Format(PyExc_ValueError,
                             "%s: output array holds %zd bytes, but the call "
                             "writes %zd (%zd items of %u bytes). Pass a "
                             "larger array, or None to have one allocated.",
                             self->info->name, have,
                             needed, count, (unsigned)element->itemsize);
                pygl_release(out);
                return -1;
            }
        }
        return 0;
    }
    (void)self;

    pygl_buf_reset(out);

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
        return pygl_array_out(self, object, element, index, *count, 0, out);
    }

    if (entry == NULL) {
        PyErr_Format(PyExc_KeyError, "Unknown specifier 0x%04X", pname);
        return -1;
    }

    pygl_buf_reset(out);

    if (entry->lookup) {
        /* The size itself comes from a runtime query.  Seven pnames in the
         * desktop table do this, so a Python call is the right cost.  dim0 is
         * how many values there are per unit the query counts:
         * MULTISAMPLE_COVERAGE_MODES_NV answers with a *pair* per mode. */
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
        if (entry->dim0) {
            *count *= (Py_ssize_t)entry->dim0;
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

    pygl_buf_reset(out);

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
    pointer = PyObject_CallMethod(pygl_support, "image_pointer", "(O)", converted);
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

/* An array whose element type the caller named.  The GL constant maps to an
 * ArrayDatatype through the same table the Python layer uses, so a type
 * registered there works here without this knowing about it. */
int pygl_array_typed(GLProc *self, PyObject *object, unsigned int type,
                     Py_ssize_t index, PyGLBuf *out)
{
    PyObject *converted, *pointer;
    void *address;
    /* The acquire helpers share one signature so that the macros can call them
     * interchangeably; this one reports through the exception the conversion
     * raised rather than composing its own, so it needs neither. */
    (void)self;
    (void)index;

    pygl_buf_reset(out);
    if (object == NULL || object == Py_None) {
        return 0;
    }
    if (pygl_is_ctypes_pointer(object)) {
        /* Already a pointer: its address is what the entry point wants, and
         * ArrayDatatype cannot answer for one. */
        void *address = pygl_pointer_slow(object);
        if (address == NULL && PyErr_Occurred()) {
            return -1;
        }
        out->owner = Py_NewRef(object);
        out->pointer = address;
        return 0;
    }
    converted = PyObject_CallMethod(pygl_support, "as_typed_array", "OI", object,
                                    type);
    if (converted == NULL) {
        return -1;
    }
    if (converted == Py_None) {
        Py_DECREF(converted);
        return 0;
    }
    pointer = PyObject_CallMethod(pygl_support, "image_pointer", "(O)", converted);
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

/* Store an argument against the current context so that it outlives the call.
 * contextdata stays a Python module: this is the once-per-batch path, not the
 * per-call one. */
int pygl_retain(GLProc *self, Py_ssize_t index, PyGLBuf *buffer)
{
    PyObject *result;
    if (buffer->owner == NULL) {
        return 0;
    }
    result = PyObject_CallMethod(pygl_support, "retain", "snO", self->info->name,
                                 index, buffer->owner);
    if (result == NULL) {
        return -1;
    }
    Py_DECREF(result);
    return 0;
}

PyObject *pygl_retained_value(PyGLBuf *buffer)
{
    if (buffer->owner == NULL) {
        Py_RETURN_NONE;
    }
    return Py_NewRef(buffer->owner);
}

void pygl_release(PyGLBuf *buffer)
{
    if (buffer->have_view) {
        PyBuffer_Release(&buffer->view);
        buffer->have_view = 0;
    }
    Py_CLEAR(buffer->owner);
    PyMem_Free(buffer->block);
    buffer->block = NULL;
    buffer->pointer = NULL;
}

/* Whether `object` is the caller's strings rather than an array of pointers
 * they built themselves: the three string types OpenGL._string_array converts,
 * and the two it takes a sequence of them in. */
static int pygl_is_strings(PyObject *object)
{
    return PyUnicode_Check(object) || PyBytes_Check(object) ||
           PyByteArray_Check(object) || PyList_Check(object) ||
           PyTuple_Check(object);
}

PyObject *pygl_string_list(const char *name, PyObject *object)
{
    PyObject *list;
    Py_ssize_t count, position;

    /* "(O)" and not "O": the format builds the argument tuple, so a caller's
     * tuple of three sources passed as "O" *is* that tuple and arrives as
     * three arguments.  Every call into the support module that passes a value
     * a caller chose says "(O)" for the same reason. */
    list = PyObject_CallMethod(pygl_support, "string_list", "(O)", object);
    if (list == NULL) {
        return NULL;
    }
    /* The contract with support.string_list is internal, which is a reason to
     * assert it rather than to assume it: PyList_GET_SIZE and
     * PyBytes_AS_STRING are unchecked macros, so a wrong return type here is a
     * crash rather than a TypeError. */
    if (!PyList_Check(list)) {
        PyErr_Format(PyExc_SystemError, "%s: string_list returned %s, not a list",
                     name, Py_TYPE(list)->tp_name);
        Py_DECREF(list);
        return NULL;
    }
    count = PyList_GET_SIZE(list);
    for (position = 0; position < count; position++) {
        PyObject *item = PyList_GET_ITEM(list, position);
        if (!PyBytes_Check(item)) {
            PyErr_Format(PyExc_SystemError,
                         "%s: string_list item %zd is %s, not bytes", name,
                         position, Py_TYPE(item)->tp_name);
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

/* A list of strings becomes a char ** for the duration of the call.  The
 * bytes objects are kept alive by the list in `owner`; the array of pointers
 * into them is this frame slot's own memory. */
int pygl_string_array(GLProc *self, PyObject *object, Py_ssize_t index,
                      PyGLBuf *out)
{
    PyObject *list;
    const char **entries;
    Py_ssize_t count, position;
    (void)index;

    pygl_buf_reset(out);
    if (object == NULL || object == Py_None) {
        return 0;
    }
    if (!pygl_is_strings(object)) {
        /* Already a char ** -- a friendly module that built the array itself,
         * which several do.  Its address is what the entry point wants;
         * rebuilding it from strings it no longer holds is not possible. */
        void *address = pygl_pointer_slow(object);
        if (address == NULL && PyErr_Occurred()) {
            return -1;
        }
        out->owner = Py_NewRef(object);
        out->pointer = address;
        return 0;
    }
    list = pygl_string_list(self->info->name, object);
    if (list == NULL) {
        return -1;
    }
    count = PyList_GET_SIZE(list);
    if (count == 0) {
        out->owner = list;
        return 0;
    }
    entries = PyMem_Calloc((size_t)count, sizeof(const char *));
    if (entries == NULL) {
        Py_DECREF(list);
        PyErr_NoMemory();
        return -1;
    }
    for (position = 0; position < count; position++) {
        entries[position] = PyBytes_AS_STRING(PyList_GET_ITEM(list, position));
    }
    out->owner = list;
    out->block = entries;
    out->pointer = entries;
    return 0;
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

/* A list, because that is what the ctypes wrapper returns and callers index,
 * append to and isinstance-check it. */
PyObject *pygl_output_tuple(PyGLBuf *buffers, const PyGLOutput *outputs,
                            Py_ssize_t count)
{
    PyObject *result = PyList_New(count);
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
        PyList_SET_ITEM(result, index, value);
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

/* A GLProc holds five references a client can set -- the ctypes binding it
 * demotes to, errcheck, a docstring, an extension override, and its instance
 * dict.  Any of them can close a cycle back to the entry point: a decorator,
 * a cache keyed by the binding, `glFoo.wrapped = thing_holding_glFoo`.  A
 * type with a settable dict and settable callbacks has to be traversable or
 * those cycles are uncollectable for the life of the process. */
static int GLProc_traverse(GLProc *self, visitproc visit, void *arg)
{
    Py_VISIT(self->ctypes_callable);
    Py_VISIT(self->errcheck);
    Py_VISIT(self->doc_override);
    Py_VISIT(self->extension_override);
    Py_VISIT(self->dict);
    return 0;
}

static int GLProc_clear(GLProc *self)
{
    Py_CLEAR(self->ctypes_callable);
    Py_CLEAR(self->errcheck);
    Py_CLEAR(self->doc_override);
    Py_CLEAR(self->extension_override);
    Py_CLEAR(self->dict);
    return 0;
}

static void GLProc_dealloc(GLProc *self)
{
    PyObject_GC_UnTrack(self);
    if (self->weakreflist != NULL) {
        PyObject_ClearWeakRefs((PyObject *)self);
    }
    Py_XDECREF(self->ctypes_callable);
    Py_XDECREF(self->errcheck);
    Py_XDECREF(self->doc_override);
    Py_XDECREF(self->extension_override);
    Py_XDECREF(self->dict);
    PyObject_GC_Del(self);
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
    /* Cheap when the answer is already known.  A lazy wrapper asks this on
     * every call it forwards, so re-reading the current context here -- which
     * costs a call into the platform layer -- would put that cost on a path
     * that has no need of it. */
    fp = pygl_current->slots[self->info->slot];
    if ((uintptr_t)fp >= PYGL_SLOT_MIN_REAL) {
        return 1;
    }
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
 * types, so an entry point answers with a Signature of its own.  It is built
 * from the parts the command already carries -- the names, and how many of them
 * a caller must supply -- rather than from the text, because a Signature built
 * out of its parts cannot fail to parse.  Built on demand: nothing on the call
 * path reads it. */
static PyObject *GLProc_get_signature(GLProc *self, void *closure)
{
    (void)closure;
    if (self->info->text_signature == NULL) {
        PyErr_SetString(PyExc_AttributeError, "__signature__");
        return NULL;
    }
    return PyObject_CallMethod(pygl_support, "signature_for", "(O)", self);
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

/* Which API this entry point belongs to.  glClear exists in GL and in GLES2 as
 * separate bindings resolved from separate libraries, so a name does not
 * identify one -- and everything in the Python layer that looks an entry point
 * up by name needs this to say which it is asking about. */
static PyObject *GLProc_get_api(GLProc *self, void *closure)
{
    (void)closure;
    return PyUnicode_FromString(pygl_api_name(self->info->api));
}

static PyObject *GLProc_get_module(GLProc *self, void *closure)
{
    (void)closure;
    return PyObject_CallMethod(pygl_support, "module_for", "ss",
                              self->info->name, pygl_api_name(self->info->api));
}

/* argtypes, restype and DLL come from the ctypes binding, which clients read
 * and wrapper.py needs.  Built on demand: nothing on the call path uses them. */
static PyObject *GLProc_ctypes_attribute(GLProc *self, const char *attribute)
{
    PyObject *callable = PyObject_CallMethod(pygl_support, "ctypes_callable", "ss",
                                             self->info->name,
                                             pygl_api_name(self->info->api));
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
    /* Not ctypes_callable: where the friendly module described customisations
     * this entry point performs in C, they were swallowed rather than applied,
     * and the binding underneath takes the arguments the registry declares
     * rather than the ones a caller passes.  support decides which of the two
     * this one is. */
    callable = PyObject_CallMethod(pygl_support, "demoted_callable", "(O)", self);
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

/* Whether `signature` -- a __text_signature__, "($module, shader, string, /)"
 * -- names `argument` as one of the arguments the entry point takes.
 *
 * A whole name, not a substring: "count" must not match "uniformCount".  What
 * may follow a name is the separator, the end of the list, or the "=None" an
 * optional output array carries. */
static int pygl_signature_takes(const char *signature, const char *argument)
{
    size_t length = strlen(argument);
    const char *at = signature;

    if (signature == NULL || length == 0) {
        return 0;
    }
    while ((at = strstr(at, argument)) != NULL) {
        char before = at == signature ? '\0' : at[-1];
        char after = at[length];
        if ((before == ' ' || before == '(') &&
            (after == ',' || after == ')' || after == ' ' || after == '=')) {
            return 1;
        }
        at += length;
    }
    return 0;
}

/* The argument a customisation call names, where it names exactly one -- the
 * 'count' of setPyConverter('count').  NULL for anything else, which the
 * caller reads as "cannot tell" and treats as the case that demotes. */
static const char *pygl_customised_argument(PyObject *args)
{
    PyObject *name;
    const char *text;
    if (args == NULL || !PyTuple_Check(args) || PyTuple_GET_SIZE(args) != 1) {
        return NULL;
    }
    name = PyTuple_GET_ITEM(args, 0);
    if (!PyUnicode_Check(name)) {
        return NULL;
    }
    text = PyUnicode_AsUTF8(name);
    if (text == NULL) {
        /* An undecodable name is one this cannot judge, not an error to
         * report: the customisation itself is about to be carried out. */
        PyErr_Clear();
    }
    return text;
}

static PyObject *GLProc_fallback(GLProc *self, PyObject *args, PyObject *kwds,
                                 const char *method)
{
    PyObject *keywords, *result;

    if (self->info->hand_written) {
        /* The C already performs what the call describes, so restating it
         * changes nothing -- *unless* the call removes an argument the C form
         * still takes.
         *
         * setPyConverter with a converter says how an argument is converted,
         * which the C does.  setPyConverter with only a name says the
         * argument is not taken from the caller at all.  Which of those two
         * that is depends on the argument: glShaderSource's C form is already
         * the two-argument one, so the module dropping `count` and `length`
         * describes what it does; dropping one it still takes builds a
         * different function with a different arity -- glVertexPointerd(array)
         * out of glVertexPointer(size, type, stride, pointer) -- which the C
         * cannot answer for.  The text signature is what separates them,
         * because it names the arguments the C form actually takes. */
        int names_one_argument =
            (strcmp(method, "setPyConverter") == 0 && args != NULL &&
             PyTuple_Check(args) && PyTuple_GET_SIZE(args) < 2);
        const char *dropped =
            names_one_argument ? pygl_customised_argument(args) : NULL;
        int drops_argument =
            names_one_argument &&
            (dropped == NULL ||
             pygl_signature_takes(self->info->text_signature, dropped));
        if (!drops_argument) {
            /* Remember it.  A module that builds a *derived* function from
             * the same entry point -- glVertexPointerd(array) out of
             * glVertexPointer(size, type, stride, pointer) -- continues the
             * chain with a call that does change the arity, and the wrapper
             * it demotes to needs the customisations swallowed before it. */
            PyObject *record = PyObject_CallMethod(pygl_support, "record_custom",
                                                   "OsO", self, method, args);
            if (record == NULL) {
                return NULL;
            }
            Py_DECREF(record);
            return Py_NewRef((PyObject *)self);
        }
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
    {"api", (getter)GLProc_get_api, NULL,
     "Which API this entry point belongs to: GL, GLES2, EGL and so on.", NULL},
    {"errcheck", (getter)GLProc_get_errcheck, (setter)GLProc_set_errcheck, NULL,
     NULL},
    {NULL}};

/* An entry point is not a method, and binding it to whatever object it was
 * reached through would be wrong -- so this hands back the entry point itself.
 * It is here for what answering __get__ at all makes true:
 * inspect.ismethoddescriptor, and so inspect.isroutine, which is the question
 * pydoc, Sphinx autodoc and PyOpenGL's own documentation generator ask before
 * deciding whether a name is a function or a piece of data.  Without it every
 * entry point documents as an assignment. */
static PyObject *GLProc_descr_get(PyObject *self, PyObject *object,
                                  PyObject *type)
{
    (void)object;
    (void)type;
    Py_INCREF(self);
    return self;
}

PyTypeObject PyGLProc_Type = {
    PyVarObject_HEAD_INIT(NULL, 0).tp_name = "OpenGL._dispatch.GLProc",
    .tp_basicsize = sizeof(GLProc),
    .tp_dealloc = (destructor)GLProc_dealloc,
    .tp_repr = (reprfunc)GLProc_repr,
    .tp_as_number = &GLProc_as_number,
    .tp_call = PyVectorcall_Call,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_VECTORCALL | Py_TPFLAGS_HAVE_GC,
    .tp_traverse = (traverseproc)GLProc_traverse,
    .tp_clear = (inquiry)GLProc_clear,
    .tp_vectorcall_offset = offsetof(GLProc, vectorcall),
    .tp_weaklistoffset = offsetof(GLProc, weakreflist),
    .tp_dictoffset = offsetof(GLProc, dict),
    .tp_getattro = PyObject_GenericGetAttr,
    .tp_setattro = PyObject_GenericSetAttr,
    .tp_descr_get = GLProc_descr_get,
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
    /* GC_New, not New: the type is tracked, and allocating a tracked object
     * through the untracked path corrupts the collector's lists. */
    GLProc *proc = PyObject_GC_New(GLProc, &PyGLProc_Type);
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
    PyObject_GC_Track(proc);
    return (PyObject *)proc;
}

static const char *const pygl_api_names[PYGL_API_COUNT] = {
    "GL", "GLES1", "GLES2", "GLES3", "GLSC2", "GLX", "WGL", "EGL"};

static const char *pygl_api_name(uint8_t api)
{
    return api < PYGL_API_COUNT ? pygl_api_names[api] : "GL";
}

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
    pygl_end_begin_block();
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
                /* The context an unclosed glBegin block belonged to is gone,
                 * so the block is over. */
                pygl_end_begin_block();
            }
            /* Empty it rather than free it: another thread may still be
             * pointing here.  Cleared slots read as unresolved, which sends
             * that thread down the slow path, and the slow path syncs the
             * context and moves it to the table it should be using. */
            if (table->slots != NULL) {
                memset(table->slots, 0, (size_t)pygl_command_count * sizeof(void *));
            }
            if (table->flags != NULL) {
                memset(table->flags, 0, (size_t)pygl_command_count);
            }
            table->handle = NULL;
            table->next = pygl_retired;
            pygl_retired = table;
            break;
        }
    }
    PyThread_release_lock(pygl_tables_lock);
    Py_RETURN_NONE;
}

/* Free every retired table, and say how many that was.
 *
 * A retired table is unreachable -- its handle is cleared, so nothing can find
 * it again -- but it is not necessarily unused: a thread that never noticed its
 * context go still points at one, and freeing under it is the use-after-free
 * retirement exists to avoid.  Nothing here can see whether such a thread
 * exists, so the judgement is the caller's, and the call is the caller making
 * it: "no thread of mine is inside a GL call, and none is dispatching through a
 * context I have destroyed".
 *
 * A program that never says so pays 43 KB per context it has destroyed, which
 * for the ordinary one or two contexts is nothing worth a decision. */
static PyObject *pygl_py_reclaim_retired(PyObject *module, PyObject *noargs)
{
    PyGLDispatch *table, *next;
    Py_ssize_t freed = 0;
    (void)module;
    (void)noargs;
    PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
    table = pygl_retired;
    pygl_retired = NULL;
    PyThread_release_lock(pygl_tables_lock);
    while (table != NULL) {
        next = table->next;
        pygl_table_free(table);
        freed++;
        table = next;
    }
    return PyLong_FromSsize_t(freed);
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

/* Set or clear a flag on every table there is: the live ones, both static
 * ones, and the default a new table is built from.  `slot` of -1 means every
 * entry point. */
static void pygl_set_flag_everywhere(int slot, uint8_t bit, int enable)
{
    PyGLDispatch *tables[2];
    PyGLDispatch *table;
    Py_ssize_t index, first, last;
    size_t which;

    first = slot < 0 ? 0 : slot;
    last = slot < 0 ? pygl_command_count - 1 : slot;
    if (enable) {
        pygl_default_flags |= bit;
    } else {
        pygl_default_flags &= (uint8_t)~bit;
    }

    tables[0] = &pygl_default_table;
    tables[1] = &pygl_null_table;
    PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
    for (table = pygl_tables; table != NULL; table = table->next) {
        if (table->flags == NULL) {
            continue;
        }
        for (index = first; index <= last; index++) {
            if (enable) {
                table->flags[index] |= bit;
            } else {
                table->flags[index] &= (uint8_t)~bit;
            }
        }
    }
    for (which = 0; which < 2; which++) {
        if (tables[which]->flags == NULL) {
            continue;
        }
        for (index = first; index <= last; index++) {
            if (enable) {
                tables[which]->flags[index] |= bit;
            } else {
                tables[which]->flags[index] &= (uint8_t)~bit;
            }
        }
    }
    PyThread_release_lock(pygl_tables_lock);
}


static PyObject *pygl_py_set_error_source(PyObject *module, PyObject *args)
{
    const char *api_name;
    PyObject *proc = Py_None;
    int slot = -1, gl_family = 0;
    unsigned int no_error = 0;
    uint8_t api;
    (void)module;
    if (!PyArg_ParseTuple(args, "siOIp", &api_name, &slot, &proc, &no_error,
                          &gl_family)) {
        return NULL;
    }
    for (api = 0; api < PYGL_API_COUNT; api++) {
        if (strcmp(pygl_api_name(api), api_name) == 0) {
            break;
        }
    }
    if (api >= PYGL_API_COUNT) {
        PyErr_Format(PyExc_ValueError, "no such API: %s", api_name);
        return NULL;
    }
    if (proc != Py_None && !PyObject_TypeCheck(proc, &PyGLProc_Type)) {
        PyErr_SetString(PyExc_TypeError,
                        "expected an OpenGL entry point or None");
        return NULL;
    }
    pygl_install_error_source(api, slot, proc, no_error, gl_family);
    Py_RETURN_NONE;
}


static PyObject *pygl_py_error_source(PyObject *module, PyObject *name)
{
    const char *api_name = PyUnicode_AsUTF8(name);
    uint8_t api;
    (void)module;
    if (api_name == NULL) {
        return NULL;
    }
    for (api = 0; api < PYGL_API_COUNT; api++) {
        if (strcmp(pygl_api_name(api), api_name) == 0) {
            const PyGLErrorSource *source = &pygl_error_sources[api];
            return Py_BuildValue("{sisIsOsO}", "slot", source->slot, "no_error",
                                 source->no_error, "active",
                                 source->active ? Py_True : Py_False,
                                 "gl_family",
                                 source->gl_family ? Py_True : Py_False);
        }
    }
    PyErr_Format(PyExc_ValueError, "no such API: %s", api_name);
    return NULL;
}


static PyObject *pygl_py_set_error_checking(PyObject *module, PyObject *args)
{
    PyObject *target = Py_None;
    int enable = 1;
    (void)module;
    if (!PyArg_ParseTuple(args, "p|O", &enable, &target)) {
        return NULL;
    }
    /* Every context, not merely the one that happens to be current: the call
     * says "turn error checking on", and a program holding several contexts
     * that got it in one of them has been told something untrue.  The default
     * moves too, so a context created afterwards agrees. */
    if (target == Py_None) {
        pygl_set_flag_everywhere(-1, PYGL_F_CHECK_ERRORS, enable);
    } else if (PyObject_TypeCheck(target, &PyGLProc_Type)) {
        pygl_set_flag_everywhere(
            (int)((GLProc *)target)->info->slot, PYGL_F_CHECK_ERRORS, enable);
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
    Py_XSETREF(pygl_ctypes_simple, Py_NewRef(simple));
    Py_XSETREF(pygl_ctypes_pointer, Py_NewRef(pointer));
    Py_XSETREF(pygl_support, Py_NewRef(support));
    /* Resolve the array classes by name into this build's own order.  The
     * index in the element table is compiled in and is ours alone; sharing a
     * *position* with a Python list meant that adding an element type there
     * silently shifted every class after it. */
    if (!PyDict_Check(array_types)) {
        PyErr_SetString(PyExc_TypeError,
                        "array_types must be a mapping of name to array class");
        return NULL;
    }
    {
        Py_ssize_t index;
        PyObject *resolved = PyList_New(PYGL_ARRAY_TYPE_COUNT);
        if (resolved == NULL) {
            return NULL;
        }
        for (index = 0; index < PYGL_ARRAY_TYPE_COUNT; index++) {
            PyObject *type =
                PyDict_GetItemString(array_types, pygl_array_type_names[index]);
            if (type == NULL) {
                Py_DECREF(resolved);
                if (!PyErr_Occurred()) {
                    PyErr_Format(PyExc_RuntimeError,
                                 "this build of the dispatch extension needs "
                                 "OpenGL.arrays.%s and it is not there; the "
                                 "extension and OpenGL are out of step, so "
                                 "rebuild PyOpenGL_accelerate",
                                 pygl_array_type_names[index]);
                }
                return NULL;
            }
            PyList_SET_ITEM(resolved, index, Py_NewRef(type));
        }
        Py_XSETREF(pygl_array_types, resolved);
    }
    /* glGetError answers for the GL family until each of them says otherwise
     * through set_error_source.  Nothing else is polled: an API whose errors
     * this cannot ask for is better unchecked than checked with GL's, which
     * would report a GL error against whichever of its calls asked next. */
    {
        static const uint8_t gl_family[] = {PYGL_API_GL, PYGL_API_GLES1,
                                            PYGL_API_GLES2, PYGL_API_GLES3,
                                            PYGL_API_GLSC2};
        size_t index;
        uint8_t api;
        for (api = 0; api < PYGL_API_COUNT; api++) {
            pygl_install_error_source(api, -1, NULL, 0u, 0);
        }
        for (index = 0; index < sizeof(gl_family) / sizeof(gl_family[0]); index++) {
            pygl_install_error_source(gl_family[index], error_slot, error_proc,
                                      0u, 1);
        }
    }
    pygl_get_current_context = (void *(*)(void))(uintptr_t)getter;
    (void)strict;  /* accepted for compatibility; the layer does not read it */
    if (pygl_default_flags) {
        Py_ssize_t index;
        PyGLDispatch *table;
        for (index = 0; index < pygl_command_count; index++) {
            pygl_null_table.flags[index] = pygl_default_flags;
            pygl_default_table.flags[index] = pygl_default_flags;
        }
        PyThread_acquire_lock(pygl_tables_lock, WAIT_LOCK);
        for (table = pygl_tables; table != NULL; table = table->next) {
            memset(table->flags, pygl_default_flags, (size_t)pygl_command_count);
        }
        PyThread_release_lock(pygl_tables_lock);
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

static PyObject *pygl_py_error_checking_suspended(PyObject *module,
                                                  PyObject *unused)
{
    (void)module;
    (void)unused;
    return PyBool_FromLong(pygl_error_suspended);
}

/* The address of the callback, so the Python side can hand it to
 * glDebugMessageCallback through the ordinary entry point. */
static PyObject *pygl_py_debug_callback_address(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    return PyLong_FromVoidPtr((void *)pygl_debug_callback);
}

/* The mode belongs to the context, so which context is current decides which
 * table this writes -- and the caller is Python, which may have made a
 * different one current since the last dispatch. */
static PyObject *pygl_py_set_error_mode(PyObject *module, PyObject *argument)
{
    long mode = PyLong_AsLong(argument);
    (void)module;
    if (PyErr_Occurred()) {
        return NULL;
    }
    pygl_sync_context();
    pygl_current->error_mode = (int)mode;
    pygl_current->audit_countdown = PYGL_DEBUG_AUDIT_INTERVAL;
    pygl_debug_pending = 0;
    Py_RETURN_NONE;
}

/* Which mechanism this context checks errors with, so the Python layer can
 * report it rather than keep a second record of what it asked for. */
static PyObject *pygl_py_error_mode(PyObject *module, PyObject *noargs)
{
    (void)module;
    (void)noargs;
    pygl_sync_context();
    return PyLong_FromLong((long)pygl_current->error_mode);
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

/* What a generated module contains, so that it can be built rather than
 * compiled and executed.  Reading a table is what makes 1,279 files
 * unnecessary. */
/* Told to us once a context exists.  Asking the platform which of EGL and GLX
 * owns the current context means probing both, and probing loads the driver --
 * 26 MB of it on this machine -- so it is not a question to answer at import,
 * when the honest answer is "none of them". */
static PyObject *pygl_py_set_context_getter(PyObject *module, PyObject *argument)
{
    unsigned long long address = PyLong_AsUnsignedLongLong(argument);
    (void)module;
    if (PyErr_Occurred()) {
        return NULL;
    }
    pygl_get_current_context = (void *(*)(void))(uintptr_t)address;
    Py_RETURN_NONE;
}

static PyObject *pygl_py_module_names(PyObject *module, PyObject *noargs)
{
    PyObject *result;
    Py_ssize_t index;
    (void)module;
    (void)noargs;
    result = PyList_New(pygl_module_count);
    if (result == NULL) {
        return NULL;
    }
    for (index = 0; index < pygl_module_count; index++) {
        PyObject *name = PyUnicode_FromString(pygl_modules[index].module);
        if (name == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, index, name);
    }
    return result;
}

/* The rows are emitted in name order, so finding one is a binary search:
 * eleven comparisons rather than the six hundred a scan averages, and every
 * friendly module asks once as it is imported. */
static const PyGLModule *pygl_module_for(const char *wanted)
{
    Py_ssize_t low = 0, high = pygl_module_count - 1;
    while (low <= high) {
        Py_ssize_t middle = low + (high - low) / 2;
        int order = strcmp(pygl_modules[middle].module, wanted);
        if (order == 0) {
            return &pygl_modules[middle];
        }
        if (order < 0) {
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }
    return NULL;
}

static PyObject *pygl_py_module_contents(PyObject *module, PyObject *argument)
{
    const char *wanted = PyUnicode_AsUTF8(argument);
    const PyGLModule *entry;
    Py_ssize_t item;
    (void)module;
    if (wanted == NULL) {
        return NULL;
    }
    {
        PyObject *enums, *commands, *reexports, *result;
        entry = pygl_module_for(wanted);
        if (entry == NULL) {
            Py_RETURN_NONE;
        }
        enums = PyDict_New();
        commands = PyList_New(entry->command_count);
        reexports = PyList_New(entry->reexport_count);
        if (enums == NULL || commands == NULL || reexports == NULL) {
            Py_XDECREF(enums);
            Py_XDECREF(commands);
            Py_XDECREF(reexports);
            return NULL;
        }
        for (item = 0; item < entry->enum_count; item++) {
            PyObject *value =
                entry->enums[item].is_signed
                    ? PyLong_FromLongLong((long long)entry->enums[item].value)
                    : PyLong_FromUnsignedLongLong(entry->enums[item].value);
            if (value == NULL ||
                PyDict_SetItemString(enums, entry->enums[item].name, value) < 0) {
                Py_XDECREF(value);
                Py_DECREF(enums);
                Py_DECREF(commands);
                Py_DECREF(reexports);
                return NULL;
            }
            Py_DECREF(value);
        }
        for (item = 0; item < entry->command_count; item++) {
            const PyGLDeclaration *command = &entry->commands[item];
            /* name, argument names, ctypes type expressions -- the last two
             * as the comma-joined text the declaration stated, split by the
             * finder only for the few entry points that ever demote. */
            PyObject *row = Py_BuildValue("(sss)", command->name,
                                          command->arguments, command->types);
            if (row == NULL) {
                Py_DECREF(enums);
                Py_DECREF(commands);
                Py_DECREF(reexports);
                return NULL;
            }
            PyList_SET_ITEM(commands, item, row);
        }
        for (item = 0; item < entry->reexport_count; item++) {
            PyObject *name = PyUnicode_FromString(entry->reexports[item]);
            if (name == NULL) {
                Py_DECREF(enums);
                Py_DECREF(commands);
                Py_DECREF(reexports);
                return NULL;
            }
            PyList_SET_ITEM(reexports, item, name);
        }
        result = Py_BuildValue("{s:s,s:N,s:N,s:N}", "extension", entry->extension,
                               "constants", enums, "commands", commands,
                               "reexports", reexports);
        return result;
    }
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
    {"reclaim_retired", pygl_py_reclaim_retired, METH_NOARGS,
     PyDoc_STR("reclaim_retired($module)\n--\n\n"
               "Free the tables of forgotten contexts; returns how many.\n\n"
               "Only safe where no thread is still dispatching through a "
               "context this process has destroyed.")},
    {"slot_address", pygl_py_slot_address, METH_O,
     "The address the current context has resolved an entry point to."},
    {"set_error_checking", pygl_py_set_error_checking, METH_VARARGS,
     "Turn per-call error checking on or off, for one entry point or all."},
    {"set_error_source", pygl_py_set_error_source, METH_VARARGS,
     PyDoc_STR("set_error_source($module, api, slot, proc, no_error, "
               "gl_family)\n--\n\n"
               "How one API is asked for its errors: its getError entry "
               "point, the code that means success, and whether its errors "
               "are GL's.")},
    {"error_source", pygl_py_error_source, METH_O,
     "What an API's error checking is set to, for tests to read back."},
    {"error_checking_suspended", pygl_py_error_checking_suspended, METH_NOARGS,
     PyDoc_STR("error_checking_suspended($module)\n--\n\n"
               "Whether this thread is inside a glBegin block.")},
    {"suspend_error_checking", pygl_py_suspend_error_checking, METH_O,
     "Suspend per-call error checking, for the duration of a glBegin block."},
    {"debug_callback_address", pygl_py_debug_callback_address, METH_NOARGS,
     "The address of the GL_KHR_debug callback, for glDebugMessageCallback."},
    {"error_mode", pygl_py_error_mode, METH_NOARGS,
     "Which mechanism the current context notices GL errors with."},
    {"set_error_mode", pygl_py_set_error_mode, METH_O,
     "0 to check with glGetError, 1 to check the GL_KHR_debug flag."},
    {"sync_context", pygl_py_sync_context, METH_NOARGS,
     "Re-read the current context from the platform and switch tables."},
    {"sync_context_fast", pygl_py_sync_context_fast, METH_NOARGS,
     "As sync_context, through the raw platform address."},
    {"set_context_getter", pygl_py_set_context_getter, METH_O,
     "Address of the platform's current-context function, once one exists."},
    {"module_names", pygl_py_module_names, METH_NOARGS,
     "Every generated module the layer can build without a file."},
    {"module_contents", pygl_py_module_contents, METH_O,
     "What one generated module contains, or None if it is not described."},
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
    Py_DECREF(error);
    return (pygl_null_function_error && pygl_no_context_error) ? 0 : -1;
}

/* The PyOpenGL version this extension's tables were generated from, supplied by
 * accelerate's setup.py.  Absent only in a build that has not been told, and a
 * build that cannot say which tables it holds is not one to dispatch through --
 * see OpenGL._dispatch._versions_match. */
#ifndef PYOPENGL_VERSION
#define PYOPENGL_VERSION "unknown"
#endif

static int pygl_exec(PyObject *module)
{
    PyObject *entry_points;

    if (PyType_Ready(&PyGLProc_Type) < 0) {
        return -1;
    }
    if (PyModule_AddStringConstant(module, "__pyopengl_version__",
                                   PYOPENGL_VERSION) < 0) {
        return -1;
    }
    pygl_tables_lock = PyThread_allocate_lock();
    if (pygl_tables_lock == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    pygl_str_asArray = PyUnicode_InternFromString("asArray");
    pygl_str_dataPointer = PyUnicode_InternFromString("dataPointer");
    pygl_str_zeros = PyUnicode_InternFromString("zeros");
    if (!pygl_str_asArray || !pygl_str_dataPointer || !pygl_str_zeros) {
        return -1;
    }
    if (pygl_init_errors() < 0) {
        return -1;
    }
    Py_INCREF(&PyGLProc_Type);
    if (PyModule_AddObject(module, "GLProc", (PyObject *)&PyGLProc_Type) < 0) {
        Py_DECREF(&PyGLProc_Type);
        return -1;
    }
    entry_points = PyDict_New();
    if (entry_points == NULL) {
        return -1;
    }
    if (pygl_register_generated(entry_points) < 0) {
        Py_DECREF(entry_points);
        return -1;
    }
    if (PyModule_AddObject(module, "entry_points", entry_points) < 0) {
        Py_DECREF(entry_points);
        return -1;
    }
    /* Both static tables need the slot count the generated code declared. */
    pygl_null_table.slots = PyMem_Calloc((size_t)pygl_command_count, sizeof(void *));
    pygl_null_table.flags = PyMem_Calloc((size_t)pygl_command_count, sizeof(uint8_t));
    pygl_default_table.slots = PyMem_Calloc((size_t)pygl_command_count, sizeof(void *));
    pygl_default_table.flags = PyMem_Calloc((size_t)pygl_command_count, sizeof(uint8_t));
    if (pygl_null_table.slots == NULL || pygl_null_table.flags == NULL ||
        pygl_default_table.slots == NULL || pygl_default_table.flags == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    return 0;
}

/* Multi-phase init, for the sake of Py_mod_gil: a module without that slot
 * makes a free-threaded interpreter re-enable the GIL for the whole process on
 * import, and PyOpenGL runs free-threaded today.  What makes the claim true is
 * that the per-context tables are the only mutable structure a call touches,
 * pygl_tables_lock guards every mutation of the registry of them, and the
 * remaining statics are set once at configure time.  The slot writes two
 * threads sharing a table can race on write the same resolved address.
 *
 * Subinterpreters are refused rather than left to fail obscurely: that same
 * process-wide state has one copy, and a second interpreter would share the
 * first one's contexts. */
static PyModuleDef_Slot pygl_module_slots[] = {
    {Py_mod_exec, (void *)pygl_exec},
#if PY_VERSION_HEX >= 0x030C0000
    {Py_mod_multiple_interpreters, Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED},
#endif
#if PY_VERSION_HEX >= 0x030D0000
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL},
};

/* After the slots, so that the slot array is a complete type here.  A
 * forward declaration of an array without its size is a GNU extension. */
static struct PyModuleDef pygl_module_def = {
    PyModuleDef_HEAD_INIT,
    .m_name = "OpenGL_accelerate.dispatch",
    .m_doc = "Registry-generated C implementation of the OpenGL entry points.",
    .m_size = 0,
    .m_methods = pygl_methods,
    .m_slots = pygl_module_slots,
};

PyMODINIT_FUNC PyInit_dispatch(void)
{
    return PyModuleDef_Init(&pygl_module_def);
}
