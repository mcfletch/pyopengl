/* C helper functions for OpenGL Numarray arrays */
#include <Python.h>
#include "numarray/libnumarray.h"
#ifdef __cplusplus
extern "C" {
#endif

static PyObject * dataPointer( PyObject * self, PyObject * args ) {
	PyObject * array = NULL;
	PyObject * result = NULL;
	char * dataPointer = NULL;
	if (!PyArg_ParseTuple( args, "O", &array )) {
		return NULL;
	}
	if (array==Py_None) {
		dataPointer = NULL;
	} else if (PyString_Check( array )) {
		/* This is undocumented, is there a better way? */
		dataPointer = ((PyStringObject *) array)->ob_sval;
	} else {
		/* XXX do a check here for array type! */
		dataPointer = ((PyArrayObject *) array)->data;
	}
	return PyInt_FromLong( (long) dataPointer );
}

static PyMethodDef _arrays_methods[] = {
	{"dataPointer", dataPointer, 1, "dataPointer( array )\n"\
								"Retrieve data-pointer value as a Python integer\n"\
								"array -- Numarray Array pointer"},
	{NULL, NULL}
};

void MODULE_INIT(void)
{
	Py_InitModule(MODULE_NAME, _arrays_methods);
	import_libnumarray();
}
#ifdef __cplusplus
}
#endif
