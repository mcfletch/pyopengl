#! /usr/bin/env python
"""Check for namespace polution..."""
from __future__ import print_function

current = set(dir())
from OpenGL.GL import *
new = set(dir())
unexpected = sorted([
    x 
    for x in (new-current-set(['current','OpenGL'])) 
    if not x.lower().startswith( 'gl' )
])

for name in unexpected:
    print(name)
