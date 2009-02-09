"""FourSuite-specific XML-documentation samples injection

Loads the manual.xml file, injects "Sample Code" sections
and re-linearises it.
"""
import sys, os
from Ft.Xml.XPath import Compile, Context
from Ft.Xml.Domlette import GetAllNs, PrettyPrint, NonvalidatingReader, implementation

import example_references

try:
	import logging
	log = logging.getLogger( 'samplemerge' )
	logging.basicConfig()
	log.setLevel( logging.INFO )
except ImportError:
	log = None

def load( source ):
	"""Load a document from source as a DOM"""
	uri = 'file:'+ os.path.abspath(source).replace( "\\", "/" )
	if log:
		log.info( "Loading source document %r", uri )
	result = NonvalidatingReader.parseUri(uri)
	if log:
		log.debug( "Finished loading document %r", uri )
	return result
def save( doc, destination ):
	if log:
		log.info( "Saving document to %r", destination )
	PrettyPrint(doc, open(destination,'w'))
	if log:
		log.debug( "Finished saving document %r", destination )
	
def find( specifier, base ):
	"""Find subnodes of base with given XPath specifier"""
	return Compile(specifier).evaluate( Context.Context( base, GetAllNs(base)) )

def main( ):
	"""Load rootFile, merge with the docs in originalDirectory and write to destination"""
	# get the sample-set by scanning directories for code...
	linkData = example_references.loadData()
	doc = load( r'S:\autobuild\PyOpenGL2\build\doc\manual_regular.xml' )
	for entry in find( "//refentry", doc ):
		functionID = entry.getAttributeNS( None, 'id' )
		log.info( "Merging samples for %s", functionID )
		# get all constant names used in the document...
		functions = {}
		for functionNode in find( 'descendant::funcprototype/descendant::function/text()', entry ):
			functions[functionNode.data] = 1
		constants = {}
		for constantNode in find( 'descendant::constant/text()', entry ):
			constants[constantNode.data] = 1
		# do we have any sample-links for this doc-node?
		functions = filter( linkData.has_key, functions.keys())
		functions.sort()
		constants = filter( linkData.has_key, constants.keys())
		constants.sort()
		# now, filter constants which don't occur in the same file as a function
		if functions:
			newNode = formatLinkSet( doc, functionID, functions, constants, linkData )
			entry.appendChild( newNode )
	save( doc, r'S:\pyopenglbuild\PyOpenGL2\build\doc\manual.xml' )




def formatLinkSet( doc, functionID, functions, constants, linkData ):
	"""Format a link-set as a set of DOM nodes"""
	base= doc.createElementNS( None, 'refsect1' )
	base.setAttributeNS(None, 'id', functionID + u'-python_samples')
	title = doc.createElementNS( None, 'title' )
	title.appendChild( doc.createTextNode( 'Python Sample Code'))
	base.appendChild( title )
	# okay, now make the actual list of sample-code links...
	p = base.appendChild( doc.createElementNS( None, 'para' ) )
	l = p.appendChild( doc.createElementNS( None, 'variablelist' ) )
	for functionName in functions:
		# linkData has information for each one of these...
		l.appendChild( formatFunctionSection( functionName, doc, linkData, functions, 0))
	for functionName in constants:
		cr = formatFunctionSection( functionName, doc, linkData, functions, 1)
		if cr:
			l.appendChild( cr )
	return base

def constantSameLine( constant, functions, linkData ):
	set = linkData.get( constant )
	result = []
	for function in functions:
		set = linkData.get( function )
		for value in set:
			line = value[-1]
			if line.find( constant ) > -1:
				result.append( value )
	return result

def formatFunctionSection( functionName, doc, linkData, functions=None, isConstant=0):
	le = doc.createElementNS( None, 'varlistentry' )
	le.appendChild( doc.createElementNS( None, 'term' ) ).appendChild(
		doc.createTextNode(functionName)
	)
	# get *unique* document refs, with meta-data for the individual line refs
	links = {}
	if isConstant:
		functionRecords = constantSameLine( functionName, functions, linkData )
		if not functionRecords:
			return None
	else:
		functionRecords = linkData[functionName]
	for (url,project,path,_,(lineNumber,_),_,lineText) in functionRecords:
		# note we are actually using a side-effect of the for loop to set url, project and path
		links.setdefault(
			project, {}
		).setdefault(
			(path,url),
			[]
		).append( lineNumber )
	links = links.items()
	links.sort()
	item = le.appendChild(doc.createElementNS( None, 'listitem'))
	projectList = item.appendChild( doc.createElementNS( None, 'itemizedlist'))
	for (project,values) in links:
		# Each project gets a "header"
		fragments = ['%s '%(project,)]
		paths = values.items()
		paths.sort()
		for (path,url),lines in paths:
			currentProject = projectList.appendChild( doc.createElementNS( None, 'listitem'))
			currentProject.appendChild( doc.createTextNode( '%s/'%(project)))
			lines.sort()
			if len(lines) > 5:
				linesText = ' Ln#%s... '%( ','.join( map(str,lines[:5])))
			else:
				linesText = ' Ln#%s '%(','.join( map(str,lines[:5])))
			# now create a description of the link...
			#  PyOpenGLDemo <a href="">NeHe/lesson6-multi.py</>Ln#3,8,15
			# currently don't support per-line links!
			link = currentProject.appendChild( doc.createElementNS( None, 'ulink'))
			link.setAttributeNS(None, 'url', url)
			link.appendChild( doc.createTextNode( path ))
			currentProject.appendChild( doc.createTextNode( linesText ) )
	return le


##	prefixedDocs = []
##	set = {}
##
##	for prefix in ['glut','glu','gle','gl']:
##		filename = os.path.join(originalDirectory, prefix.upper(), 'reference.xml')
##		doc = load(filename)
##		for node in find( "//*[@id]", doc ):
##			set[ node.getAttributeNS(None,'id')] = node
##		prefixedDocs.append( (prefix, doc))
##	doc = load( rootFile )
##	for entry in find( "//*[@condition='replace']", doc ):
##		# now, for each refentry, there is an "original" entry
##		# from which we copy 90% of the data...
##		id = entry.getAttributeNS(None,'id')
##		if log:
##			log.debug( "substitution for %r", id )
##		original = set.get( id )
##		if not original:
##			if log:
##				log.warn( "Unable to find substitution source for %r", id )
##			continue; # next entry
##		entry.parentNode.replaceChild( original, entry )
##
##	# now set the version #
##	for node in find( "application[@condition='version']", doc ):
##		node.nodeValue = node.nodeValue + str(version)
##
##	doctype = implementation.createDocumentType(
##		"book",
##		"-//OASIS//DTD DocBook MathML Module V1.0//EN",
##		"http://www.oasis-open.org/docbook/xml/mathml/1.0/dbmathml.dtd",
##	)
##	newdoc = implementation.createDocument( "ISO-8859-1", "book", doctype )
##	newdoc.replaceChild( doc.documentElement, newdoc.documentElement )
##	save( newdoc, destination )

if __name__ == "__main__":
	main(
	)

