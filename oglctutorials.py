#! /usr/bin/env python
"""Generate the OpenGLContext shader tutorials from '''-string marked-up source code"""
import re,os,sys,textwrap, datetime
import kid, logging
log = logging.getLogger( 'tutorials' )

text_re = re.compile(
    r"""^[ \t]*(''')(?P<commentary>.*?)(''')[ \t]*$""",
    re.MULTILINE|re.I|re.DOTALL
)
block_splitter = re.compile(r"""\n[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
empty_line_matcher = re.compile(r"""[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
markup_re = re.compile(
    r"""\[(?P<url>[^ ]+)[ ]+(?P<link_text>[^]]+)\]"""
)
image_extensions = [ '.png','.jpg','.bmp','.tif' ]

import OpenGLContext
test_dir = os.path.join(
    os.path.dirname( OpenGLContext.__file__ ),
    '..',
    'tests',
)

OUTPUT_DIRECTORY=os.path.join(
    os.path.dirname( OpenGLContext.__file__ ),
    '..',
    'docs',
    'tutorials',
)
if not os.path.isdir( OUTPUT_DIRECTORY ):
    os.makedirs( OUTPUT_DIRECTORY )

serial = kid.XHTMLSerializer( decl=True )

def generate_index( paths ):
    """Generate index file for given paths"""
    next = paths[0].children[0]
    prev = paths[-1].children[-1]

    template = kid.Template(
        file='templates/tutorialindex.kid',
        paths=paths,
        next = next,
        prev = prev,
        date=datetime.datetime.now().strftime( '%Y-%m-%d' ),
        version = OpenGLContext.__version__,
    )
    data = template.serialize( output=serial )
    html_file = os.path.join( OUTPUT_DIRECTORY, 'index.xhtml' )
    print 'writing', html_file
    open( html_file, 'w').write( data )


def generate( tutorial, prev=None, next=None, path=None ):
    template = kid.Template(
        file='templates/tutorial.kid',
        tutorial = tutorial,
        date=datetime.datetime.now().isoformat(),
        path = path,
        prev=prev,
        next=next,
    )
    data = template.serialize( output=serial )
    print 'writing', tutorial.html_file
    open( tutorial.html_file, 'w').write( data )


class Block( object ):
    """Block of text for presentation"""
    html_tag = 'div'
    html_class = ''
    def __init__( self, text=None, children=None, tail=None ):
        """Initializes the block of text with given text"""
        self.text = text
        self.children = children
        self.tail = tail
        if self.text:
            self.text, children = self.markup( self.text )
            if not self.children:
                self.children = children
            else:
                self.children[:0] = children
    def markup( self, text ):
        """Returns text, children"""

        new_text, children = "",[]
        offset = 0
        for match in markup_re.finditer( text ):
            if not offset:
                new_text = text[:match.start()]
            else:
                if children[-1].tail is None:
                    children[-1].tail = text[offset:match.start()]
                else:
                    children[-1].tail += text[offset:match.start()]
            offset = match.end()
            if match.group( 'url' ):
                url = match.group( 'url' )
                cls = Anchor
                for suffix in image_extensions:
                    if url.endswith( suffix ):
                        cls = Image
                children.append( cls(
                    match.group( 'link_text' ),
                    url,
                ))
            else:
                raise RuntimeError( "Unknown markup: %s", text )
        if not offset:
            return text, children
        else:
            if children[-1].tail is None:
                children[-1].tail = text[offset:]
            else:
                children[-1].tail += text[offset:]
        return new_text, children
    def append( self, value ):
        """Append given value to our content"""
        if isinstance( value, (str,unicode)):
            if self.children:
                last_child = self.children[-1]
                if last_child.tail:
                    last_child.tail += value
                else:
                    last_child.tail = value
            elif self.text:
                self.text += value
            else:
                self.text = value
            return True
        else:
            # is a node of some form...
            self.children.append( value )

class Grouping( Block ):
    def __init__( self,*args,**named ):
        super( Grouping, self ).__init__(*args,**named)
        if self.children is None:
            self.children = []

class TutorialPath( Grouping ):
    """Path through a series of tutorials"""
    def generate_children( self ):
        first = self.children
        for i in range( len(first)):
            next = prev = None
            if i > 0:
                prev = first[i-1]
            if i < len(first)-1:
                next = first[i+1]
            generate( first[i], next=next,prev=prev, path=self )

class Tutorial( Grouping ):
    html_tag = 'body'
    html_class = 'tutorial'
    @property
    def title( self ):
        """find our first title descendant"""
        for item in self.children:
            if isinstance( item, Commentary ):
                for child in item.children:
                    if isinstance( child, Title ):
                        return child.text
        return "No title found"
    def set_file( self, filename ):
        base = os.path.basename( filename )
        self.filename = base
        root = os.path.splitext( base )[0]
        self.html_file = os.path.join(
            OUTPUT_DIRECTORY, '%s.xhtml'%(root)
        )
        self.relative_link = '%s.xhtml'%( root, )

class Title( Block ):
    html_tag = 'h1'
    html_class = 'title'

class Commentary( Grouping ):
    """Used for human commentary"""
    html_tag = 'div'
    html_class = 'commentary'
    def __init__( self,text=None,*args,**named ):
        commentary = text
        text = None
        super( Commentary, self ).__init__(text,*args,**named)
        blocks = block_splitter.split( commentary )
        for block in blocks:
            block = textwrap.dedent( block )
            if block.startswith( '*' ):
                ul = UL()
                li = None
                self.append( ul )
                for line in block.splitlines():
                    if line.startswith( '*' ):
                        li = LI( line[1:].lstrip())
                        ul.append( li )
                    else:
                        if li:
                            li.append( line )
            elif block.startswith( '=' ) and block.endswith( '=' ):
                self.append( Title( block.strip( '=' ).strip() ))
            else:
                self.append( Paragraph( block ))

class Code( Block ):
    """Used for machine-executable code"""
    html_tag = 'div'
    html_class = 'code-sample'
    def markup( self, text ):
        return text, None
class Paragraph( Block ):
    """Generic paragraph in commentary"""
    html_tag = 'div'
    html_class = 'paragraph'
class UL( Grouping ):
    """Unordered list in commentary"""
    html_tag = 'ul'
class LI( Block ):
    """Unordered list item in UL"""
    html_tag = 'li'

class Anchor( Block ):
    """Simple url link/anchor value"""
    html_tag = 'a'
    def __init__( self, text, url ):
        super( Anchor, self ).__init__( text )
        self.url = url

class Image( Anchor ):
    html_tag = 'img'


def parse_file( filename ):
    text = open( filename ).read()
    tutorial = Tutorial()
    tutorial.set_file( filename )
    offset = 0
    for match in text_re.finditer( text ):
        py_text = text[ offset: match.start()]
        empty_match = empty_line_matcher.match( py_text )
        if empty_match:
            py_text = py_text[empty_match.end():]
        if py_text.strip():
            tutorial.append( Code( py_text ) )
        if match.group( 'commentary' ).strip():
            tutorial.append(
                Commentary( match.group('commentary') )
            )
        offset = match.end()
    if text[offset:].strip():
        tutorial.append( Code( text[ offset:] ) )
    return tutorial

if __name__ == "__main__":
    shaders = TutorialPath(
        "Introduction to Shaders",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'shader_intro.py',
                'shader_1.py',
                'shader_2.py',
                'shader_3.py',
                'shader_4.py',
                'shader_5.py',
                'shader_6.py',
                'shader_7.py',
                'shader_8.py',
                'shader_9.py',
                'shader_10.py',
                'shader_11.py',
                'shader_12.py',
            ]
        ]
    )
    effects = TutorialPath(
        "Depth-map Shadows",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'shadow_1.py',
                'shadow_2.py',
            ]
        ],
    )
    nodes = TutorialPath(
        "Scenegraph Nodes",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'lightobject.py',
                'molehill.py',
                'nurbsobject.py',
                'particles_simple.py',
            ]
        ]
    )
    nehe = TutorialPath(
        "NeHe Translations",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'nehe1.py',
                'nehe2.py',
                'nehe3.py',
                'nehe4.py',
                'nehe5.py',
                'nehe6.py',
                'nehe7.py',
                'nehe8.py',
                'nehe6_timer.py',
                'nehe6_multi.py',
                'glprint.py',
            ]
        ]
    )
    paths = [shaders,nodes,effects,nehe]
    generate_index( paths = paths )
    for path in paths:
        path.generate_children()

