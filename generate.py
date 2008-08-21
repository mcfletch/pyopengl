#! /usr/bin/env python
import glob, os, datetime
#import elementtree.ElementTree as ET
import lxml.etree as ET
import kid

from directdocs.model import Function, Parameter, ParameterReference
from directdocs import model
from OpenGL import __version__
from OpenGL import GL, GLU, GLUT, GLE

IMPORTED_PACKAGES = [GL,GLU,GLUT,GLE]
PACKAGES = ['GL','GLU','GLUT','GLE',]

DOCBOOK_NS = 'http://docbook.org/ns/docbook'
MML_NS = "http://www.w3.org/1998/Math/MathML"

WRAPPER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book SYSTEM "test" [ <!ENTITY nbsp " "> ]>

<book 
	xmlns="%s"
	xmlns:mml="%s">
%%s
</book>"""%( DOCBOOK_NS, MML_NS )

class Reference( model.Reference ):
	"""Reference class with doc-set-specific coding"""
	def get_crossref( self, title, volume=None,section=None ):
		key = '%s.%s'%(title,volume)
		if '(' in title:
			title = title.split('(')[0]
		if self.sections.has_key( key ):
			return self.sections[key]
		elif self.section_titles.has_key( title ):
			return self.section_titles[ title ]
		elif self.functions.has_key( title ):
			return self.functions[title]
		elif title.startswith( 'glX') or title.startswith( 'wgl' ):
			print 'Reference to', title, 'in', getattr(section,'title','Unknown')
			return None
		else:
			# try a linear scan for suffixed version...
			for name in self.functions.keys():
				if self.suffixed_name( name, title ) or self.suffixed_name( title,name ):
					return self.functions[name]
			return None
			raise KeyError( 'Function %s referenced from %s not found'%(key, getattr(section,'title','Unknown') ))
	def url( self, target ):
		if isinstance( target, RefSect ):
			return './%s.xhtml'%(target.title,)
		elif isinstance( target, model.PyFunction ):
			return '%s#py-%s'%(self.url(target.section),target.name)
		elif isinstance( target, Function ):
			return '%s#c-%s'%(self.url(target.section),target.name)
		raise ValueError( """Don't know how to create url for %r"""%(target,))
	def package_names( self ):
		return PACKAGES
	def modules( self ):
		return IMPORTED_PACKAGES

class RefSect( model.RefSect ):
	query_namespace = {
		'd':DOCBOOK_NS,
		'm':MML_NS,
	}
	def process( self, tree ):
		processors = {
		}
		for function in dir(self):
			if function.startswith( 'process_' ):
				key = '{%s}%s'%(DOCBOOK_NS,function[8:])
				value = getattr( self, function )
				processors[key ] = value
		self.id = tree[0].get('id')
		self.title = self.name = tree[0].xpath( './/d:refmeta/d:refentrytitle', self.query_namespace )[0].text
		self.functions = dict([
			(x.text,Function(x.text,self))
			for x in tree[0].xpath( 
				'.//d:refnamediv/d:refname', self.query_namespace 
			)
		])
		self.purpose = tree[0].xpath( 
			'.//d:refnamediv/d:refpurpose',self.query_namespace
		)[0].text
		for func_prototype in tree[0].xpath(
			'.//d:refsynopsisdiv/d:funcsynopsis/d:funcprototype',
			self.query_namespace 
		):
			self.process_funcprototype( func_prototype )
		processed_sections = {}
		for section in tree[0].xpath( './/d:refsect1', self.query_namespace):
			id = section.get( 'id' )
			if '-parameters' in id:
				for varlist in section.xpath( './d:variablelist',self.query_namespace):
					self.process_variablelist( varlist )
			elif id.endswith( '-see_also' ):
				for entry in section.xpath( './/d:citerefentry',self.query_namespace):
					title,volume = entry[0].text, entry[1].text
					self.see_also.append( (title,volume) )
			else:
				self.discussions.append( section )
			processed_sections[ id ] = True

		#for element in tree.iterdescendants():
		#	if element.tag in processors:
		#		processors[element.tag]( element )
		#	else:
		#		'no processor for', element.tag
	def process_refentry( self, node ):
		if not self.id:
			self.id = node.get( 'id' )
	def process_refentrytitle( self, node ):
		if not self.title:
			self.title = node.text
	def process_refpurpose( self, node ):
		if not self.purpose:
			self.purpose = node.text
	def process_refname( self, node ):
		self.functions[ node.text ] = Function(node.text.strip())
	def process_funcprototype( self, node ):
		funcdef = node[0]
		params = node[1:]
		return_value = funcdef.text.strip()
		for child in funcdef:
			funcname = child.text
		paramresults = []
		for param in params:
			if not param.tag.endswith( '}void' ):
				typ = param.text 
				for item in param:
					paramname = item.text 
					if item.tail:
						typ += item.tail
				try:
					paramresults.append( Parameter(
						data_type = typ,
						name = paramname
					))
				except Exception, err:
					print 'Failure retrieving parameter:', str(param)
		try:
			function = self.functions[ funcname ]
		except KeyError, err:
			err.args += (self.functions.keys(),)
			raise
		function.return_value = return_value
		function.parameters = paramresults
		for param in paramresults:
			param.function = function
	def process_variablelist( self, node ):
		"""Process a variable list into annotations"""
		set = []
		for entry in node:
			terms = []
			description = ''
			for item in entry:
				if item.tag.endswith( 'term' ):
					value = "".join( [x.text.strip() for x in item.iterdescendants() if x.text] )
					terms.append(value)
				else:
					description = item	
			set.append( ParameterReference(terms,description))

		self.varrefs.extend( set )

def load_file( filename ):
	data = WRAPPER%(open(filename).read())
	return ET.XML( data )


def main():
	files = []
	for package in PACKAGES:
		files.extend(
			[(package,x) for x in glob.glob( 'original/%s/*.xml'%package )]
		)
	files.sort()
	ref = Reference()
	for package,path in files:
		#print 'loading', path
		tree = load_file( path )
		r = RefSect( package, ref )
		r.process( tree )
		ref.append( r )
	
#		print r.id,r.title,r.purpose
#		for name,spec in r.functions.items():
#			print '\t', name 
#			print '\t\t',spec
#		for varref in r.varrefs:
#			print varref
	ref.check_crossrefs()
	# now generate some files...
	serial = kid.XHTMLSerializer( decl=True )
	template = kid.Template( 
		file='templates/index.kid', 
		ref=ref, 
		date=datetime.datetime.now().isoformat(),
		version=__version__,
	)
	data = template.serialize( output=serial )
	open( 'output/index.xhtml', 'w').write( data )

	for name,section in ref.sections.items():
		template = kid.Template(
			file = 'templates/section.kid',
			ref=ref,
			section=section,
			date=datetime.datetime.now().isoformat(),
			version=__version__,
		)
		data = template.serialize( output=serial )
		open( 'output/%s'%(ref.url(section)), 'w').write( data )

if __name__ == "__main__":
	main()

