template = '''class %(typeName)sArray( ArrayDatatype, ctypes.POINTER(constants.%(typeName)s )):
	"""Array datatype for %(typeName)s types"""
	baseType = constants.%(typeName)s
	typeConstant = constants.%(constantName)s
'''
from OpenGL import constants 

def printType( typeName, constant ):
	constantName = constant.name
	print template%locals()

if __name__ == "__main__":
	items = constants.ARRAY_TYPE_TO_CONSTANT
	for key,value in items:
		printType( key,value )
	print 'GL_CONSTANT_TO_ARRAY_TYPE = {'
	for key,value in items:
		print '\tconstants.%s : %sArray,'%(value.name,key)
	print '}'

