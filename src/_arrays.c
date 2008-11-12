/* C helper functions for OpenGL Numeric arrays */
#include "Python.h"
#ifdef USE_NUMPY
#include "numpy/arrayobject.h"
#else
#include "Numeric/arrayobject.h"
#endif

#ifdef __cplusplus
extern "C" {
#endif

static PyObject * dataPointer( PyObject * self, PyObject * args ) {
	PyObject * array = NULL;
	char * dataPointer = NULL;
	if (!PyArg_ParseTuple( args, "O", &array )) {
		return NULL;
	}
	if (array==Py_None) {
		dataPointer = NULL;
	} else {
		/* XXX do a check here for array type! */
		dataPointer = ((PyArrayObject *) array)->data;
	}
	return PyInt_FromLong( (long) dataPointer );
}

static PyMethodDef _arrays_methods[] = {
	{"dataPointer", dataPointer, 1, "dataPointer( array )\n"\
								"Retrieve data-pointer value as a Python integer\n"\
								"array -- Numeric Array pointer"},
	{NULL, NULL}
};

#ifdef USE_NUMPY
void
initnumpy_accel(void)
{
	Py_InitModule("numpy_accel", _arrays_methods);
	import_array();
}
#else
void
inittnumeric_accel(void)
{
	Py_InitModule("numeric_accel", _arrays_methods);
	import_array();
}
#endif

#ifdef __cplusplus
}
#endif
