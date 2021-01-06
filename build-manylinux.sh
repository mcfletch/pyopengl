#! /bin/bash

docker run \
    -it \
    -v`pwd`:/io \
    -ephemeral \
    -ePLAT=manylinux2014_x86_64 \
    --rm \
    quay.io/pypa/manylinux2014_x86_64 \
    /io/accelerate/_build-manylinux.sh
