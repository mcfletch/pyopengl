#! /bin/bash

rsync -avP -e ssh manual-3.1/* mcfletch,pyopengl@web.sourceforge.net:htdocs/documentation/manual-3.0/
