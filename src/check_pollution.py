#! /usr/bin/env python
"""Check for namespace polution..."""

current = set(dir())
from OpenGL.GL import *
new = set(dir())
unexpected = sorted([
    x 
    for x in (new-current-set(['current','OpenGL'])) 
    if not x.lower().startswith( 'gl' )
])

for name in unexpected:
    print name
