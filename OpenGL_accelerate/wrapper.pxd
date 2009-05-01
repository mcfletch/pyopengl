"""Importable declarations for wrapper module"""

cdef class cArgConverter:
	"""C-level API definition for cConverter objects"""
	cdef object c_call( self, tuple pyArgs, int index, object baseOperation )

