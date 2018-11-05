#! /bin/bash

COMMIT=$(git show-ref --head HEAD | cut -f 1 -d" ")
appveyor-artifacts \
	-c $COMMIT \
	-o MikeCFletcher \
	-n pyopengl \
	--dir ./dist \
	--no-job-dirs skip \
	-v \
	download
