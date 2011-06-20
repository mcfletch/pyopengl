#! /usr/bin/env python
"""Quick script to check for all entry points being defined"""
import re,pprint,logging
lmatch= re.compile( r'^\w+[ \t]*\([^)]+\)' )
comment = re.compile( r'([ \t]*\#.*)|passthru\:' )
param = re.compile( r'[ \t]+(?P<type>[^ \t]+)[ \t]+(?P<name>[^ \t]+)([ \t]+(?P<details>.*))?' )
functions = {}
log = logging.getLogger( 'missing' )

def module_for_category( category ):
    """Return the OpenGL.GL.x module for the given category name"""
    if category.startswith( 'VERSION_' ):
        name = 'OpenGL.GL'
    else:
        owner,name = category.split( '_',1)
        if owner.startswith( '3' ):
            owner = owner[1:]
        name = 'OpenGL.GL.%s.%s'%( owner,name )
    return __import__( name, {}, {}, name.split( '.' ))


def main():
    current = None 
    for line in open( 'gl.spec' ):
        line = line.rstrip( '\n' ).rstrip( '\r' )
        if lmatch.match( line ):
            current = {
                '': line.strip()
            }
            functions[line.strip()] = current
        elif not current:
            pass
        elif comment.match( line ):
            pass 
        else:
            match = param.match( line )
            if match:
                current.setdefault(match.group('type'),[]).append(
                    (match.group('name'),match.group('details'))
                )
    categories = {}
    for key,func in functions.items():
        assert 'category' in func, func
        categories.setdefault(
            func['category'][0][0],
            [] 
        ).append( func )
    for category,funcs in sorted(categories.items()):
        try:
            module = module_for_category( category )
        except ImportError, err:
            log.error( 'Whole category missing: %s', category )
        else:
            log.info( 'Checking category: %s', category )
            for func in funcs:
                funcname = func[''].split('(')[0]
                funcname = 'gl'+funcname
                if not hasattr( module, funcname ):
                    log.error(
                        "Missing entry point %s in module %s",
                        funcname,
                        module.__name__,
                    )

if __name__ == "__main__":
    logging.basicConfig()
    main()
