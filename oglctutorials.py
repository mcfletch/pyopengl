#! /usr/bin/env python
"""Generate the OpenGLContext shader tutorials from '''-string marked-up source code"""
import re,os,sys,textwrap
text_re = re.compile(
	r"""^[ \t]*(''')(?P<commentary>.*?)(''')[ \t]*$""",
	re.MULTILINE|re.I|re.DOTALL
)
block_splitter = re.compile(r"""\n[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
empty_line_matcher = re.compile(r"""[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)

def as_html( commentary ):
	result = []
	blocks = block_splitter.split( commentary )
	for block in blocks:
		block = textwrap.dedent( block )
		if block.startswith( '*' ):
			result.append( '<ul>' )
			started = False
			for line in block.splitlines():
				if line.startswith( '*' ):
					if started:
						result.append( '</li>' )
					result.append( '<li>' )
					started = True 
					result.append( line[1:].strip() )
				else:
					result.append( line.strip() )
			if started:
				result.append( '</li>' )
			result.append( '</ul>' )
		else:
			result.append( '<div>' )
			result.append( block )
			result.append( '</div>' )
	return "\n".join( result )
def process_file( filename ):
	text = open( filename ).read()
	base = os.path.basename( filename )
	root = os.path.splitext( base )[0]
	html_file = os.path.join( 'tutorials', '%s.html'%(root) )
	python_file = os.path.join( 'tutorials', base )
	print 'writing', html_file
	print 'writing', python_file
	html = open( html_file, 'w')
	html.write( '''<html><head><link rel="stylesheet" href="tutorial.css" type="text/css" /></head><body>''' )
	python = open( python_file, 'w')
	offset = 0
	def add( py_text=None, commentary=None ):
		if py_text:
			python.write( py_text )
			empty_match = empty_line_matcher.match( py_text )
			if empty_match:
				py_text = py_text[empty_match.end():]
			html.write( '<div class="code-sample">' )
			html.write( py_text )
			html.write( '</div>' )
		if commentary:
			html.write( '<div class="commentary">' )
			html.write( as_html( commentary) )
			html.write( '</div>' )
			
	for match in text_re.finditer( text ):
		py_text = text[ offset: match.start()]
		add( py_text, match.group('commentary') )
		offset = match.end()
	add( text[ offset:] )
	python.close()
	html.write('</body></html>')
	html.close()

if __name__ == "__main__":
	process_file(  sys.argv[1] )
