#! /bin/bash

COMMIT=$(git show-ref HEAD | cut -f 1 -d" ")
appveyor-artifacts -c $COMMIT -o MikeCFletcher -n pyopengl -v download
