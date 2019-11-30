#! /bin/bash

# COMMIT=$(git show-ref --head HEAD | cut -f 1 -d" ")
appveyor-dist \
	-u MikeCFletcher \
	-p pyopengl \
	--dist dist
