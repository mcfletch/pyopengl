"""Simplistic wiki-like format parsing support"""
from __future__ import absolute_import
import re,os,sys,textwrap, datetime
import logging
import six
log = logging.getLogger( __name__ )

text_re = re.compile(
    r"""^[ \t]*?(''')(?P<commentary>.*?)(''')[ \t]*?$""",
    re.MULTILINE|re.I|re.DOTALL
)
block_splitter = re.compile(r"""\n[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
empty_line_matcher = re.compile(r"""[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
markup_re = re.compile(
    r"""\[(?P<url>[^ ]+)[ ]+(?P<link_text>[^]]+)\]|(?P<bald_url>http\:\/\/[^ \t\n]+)"""
)
image_extensions = [ '.png','.jpg','.bmp','.tif' ]
dl = re.compile( r"""[ \t]*(?P<term>\w+)\W*[-][-]\W*(?P<def>.*)""" )

def format_docstring( docstring ):
    """Turn docstring into human commentary structures"""
    return Commentary( docstring )

def markup( text, child_function ):
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
        children.append( child_function( match ))
    if not offset:
        return text, children
    else:
        if children[-1].tail is None:
            children[-1].tail = text[offset:]
        else:
            children[-1].tail += text[offset:]
    return new_text, children

class Block( object ):
    """Block of text for presentation"""
    html_tag = 'div'
    html_class = ''
    def __init__( self, text=None, children=None, tail=None, cls=None ):
        """Initializes the block of text with given text"""
        self.text = text
        self.children = children
        self.tail = tail
        if cls:
            self.html_class = self.html_class + ' ' + cls 
        if self.text:
            self.text, children = self.markup( self.text )
            if not self.children:
                self.children = children
            else:
                self.children[:0] = children
    def markup( self, text ):
        """Returns text, children"""
        def child_function( match ):
            if match.group( 'url' ):
                url = match.group( 'url' )
                cls = Anchor
                for suffix in image_extensions:
                    if url.endswith( suffix ):
                        cls = Image
                return cls(
                    match.group( 'link_text' ),
                    url,
                )
            elif match.group( 'bald_url' ):
                url = match.group( 'bald_url' )
                return Anchor(
                    url,
                    url,
                )
            else:
                raise RuntimeError( "Unknown markup: %s", text )
        return markup( text, child_function )
    def append( self, value ):
        """Append given value to our content"""
        if isinstance( value, (str,six.text_type)):
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

class Title( Block ):
    html_tag = 'h1'
    html_class = 'title'

def indent_level( block ):
    """Number of characters of indent"""
    block = block.replace( '\t',' '*8)
    line = block.lstrip( ' ' )
    return len(block) - len(line)

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
            level = indent_level( block )
            cls='indent-level-%s'%(level,)
            block = textwrap.dedent( block )
            if block.startswith( '*' ) or block.startswith( '-' ):
                ul = UL(cls=cls)
                li = None
                self.append( ul )
                for line in block.splitlines():
                    if line.startswith( '*' ) or line.startswith( '-'):
                        li = LI( line[1:].lstrip())
                        ul.append( li )
                    else:
                        if li:
                            li.append( line )
            elif dl.match( block ):
                dlist = DL( cls=cls )
                self.append( dlist )
                dd = None
                for line in block.splitlines():
                    match = dl.match( line )
                    if match:
                        dlist.append( DT( match.group('term')))
                        dd = DD( match.group('def'))
                        dlist.append( dd )
                    else:
                        if dd:
                            dd.append( line )
            elif block.startswith( '=' ) and block.endswith( '=' ):
                self.append( Title( block.strip( '=' ).strip(), cls=cls ))
            elif block.startswith( '_' ) and block.endswith( '_' ):
                title = Title( block.strip( '_' ).strip(), cls=cls )
                title.html_tag= 'h2'
                self.append( title )
            else:
                self.append( Paragraph( block,cls=cls ))

class Code( Block ):
    """Used for machine-executable code"""
    html_tag = 'div'
    html_class = 'code-sample'
    def markup( self, text ):
        return text, None
class CollapsedCode( Code ):
    html_class = 'code-sample collapsed'
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

class DL( Grouping ):
    html_tag = 'dl'
class DT( Block ):
    html_tag = 'dt'
class DD( Block ):
    html_tag = 'dd'

class Anchor( Block ):
    """Simple url link/anchor value"""
    html_tag = 'a'
    def __init__( self, text, url ):
        super( Anchor, self ).__init__( text )
        self.url = url
    def markup( self, text ):
        return self.text, []

class Image( Anchor ):
    html_tag = 'img'
