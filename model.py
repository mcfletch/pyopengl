"""Modelling objects for the documentation generator"""

class Reference( object ):
	"""Overall reference text"""
	def __init__( self ):
		self.sections = {}
		self.section_titles = {}
		self.functions = {}
		self.constants = {}
	def append( self, section ):
		"""Add the given section to our tables"""
		self.sections[section.id] = section
		self.section_titles[section.title]= section
		for function in section.functions.values():
			self.functions[ function.name ] = function 
	
	def suffixed_name( self, a,b ):
		"""Is b a with a suffix?"""
		if b.startswith( a ):
			for char in b[len(a):]:
				if char not in self.suffix_chars:
					return False 
			return True 
		return False
	def get_crossref( self, title, volume=None,section=None ):
		raise NotImplemented( """Need a get_crossref method""" )
	def package_names( self ):
		raise NotImplemented( """Need a package_names method""" )
	def modules( self ):
		raise NotImplemented( """Need a modules method""" )

	suffix_chars = 'iufs1234v'
	def check_crossrefs( self ):
		sections = sorted(self.sections.items())
		for i,(name,section) in enumerate(sections):
			list(section.get_crossrefs(self))
			if i > 0:
				section.previous = sections[i-1][1]
			if i < len(sections)-1:
				section.next = sections[i+1][1]
			section.find_python_functions()

	def packages( self ):
		result = []
		for source in self.package_names():
			result.append( (source,sorted([
				(name,section) for name,section in self.section_titles.items()
				if section.package == source 
			])))
		return result

class RefSect( object ):
	id = None 
	title = None
	purpose = None
	next = None
	previous = None
	def __init__( self, package='GL', reference=None ):
		self.package = package
		self.reference = reference
		self.functions = {}
		self.varrefs = []
		self.see_also = []
		self.discussions = []
	def get_module( self ):
		"""Retrieve our module"""
		return self.reference.modules()[ 
			self.reference.package_names().index( self.package ) 
		]
	def get_crossrefs( self, reference ):
		"""Retrieve all cross-references from reference"""
		for (title,volume) in self.see_also:
			target = reference.get_crossref( title, volume, self )
			if target is not None:
				yield target
		# should also look for mentions in the description sections
	def find_python_functions( self ):
		"""Find our functions, aliases and the like in python module"""
		# TODO this is a very inefficient scan...
		source = self.get_module()
		for name,function in sorted(self.functions.items()):
			if hasattr( source, function.name ):
				function.python[name] = PyFunction(
					root_function = function,
					py_function = getattr( source,name ),
					alias = name,
				)
				for name in sorted(dir(source)):
					if (
						self.reference.suffixed_name( name, function.name ) or 
						self.reference.suffixed_name( function.name, name )
					):
						if not self.functions.has_key( name ):
							function.python[name] = PyFunction(
								root_function = function,
								py_function = getattr( source,name ),
								alias = name,
							)
							if not self.reference.functions.has_key( name ):
								self.reference.functions[ name ] = function

class Function( object ):
	"""Function description produced from docs
	
	Each function represents an original OpenGL function,
	which may have many Python-level functions associated
	with it.
	"""
	return_value = None 
	def __init__( self,name, section ):
		self.name = name
		self.section = section
		self.python = {} # name to python function...
		self.parameters = []
	def __repr__( self ):
		return '%s( %s ) -> %s'%(
			self.name, 
			self.parameters,
			self.return_value,
		)

class PyFunction( Function ):
	"""Python-implemented function produced via introspection"""
	def __init__( self, root_function, py_function, alias=None ):
		self.root_function = root_function 
		self.py_function = py_function
		self.alias = alias
	@property
	def name( self ):
		"""Introspect to get a name for our function"""
		if self.alias:
			return self.alias 
		# okay, so do some introspection...
		if hasattr( self.py_function, '__name__' ):
			return self.py_function.__name__
		raise ValueError( """Don't know how to get name for %r type"""%(
			self.py_function.__class__,
		))
	@property 
	def section( self ):
		return self.root_function.section 
	@property 
	def python( self ):
		return {}
	@property 
	def parameters( self ):
		"""Calculate (and store) parameter-list for the function"""
		return []
	@property 
	def return_value( self ):
		"""Determine (if possible) whether we have a return-value type"""
		if hasattr( self.py_function, 'restype' ):
			return self.py_function.restype 
		return None

class Parameter( object ):
	"""Description of a parameter to a function"""
	def __init__( self, name, description=None,data_type=None,function=None ):
		"""Initialize with the values for the parameter"""
		self.function = function 
		self.data_type = data_type
		self.name = name 
		self.description = description

class ParameterReference( object ):
	def __init__( self, names, description ):
		self.names = names 
		self.description = description
	def __repr__( self ):
		result = []
		return '\t\t%s -- %s'%( ', '.join(self.names), self.description )

