#!/bin/bash

ARCH=$(uname -m)
if [ "$ARCH" == "x86_64" ]; then
  MANYLINUX="manylinux_2_28_x86_64"
elif [ "$ARCH" == "aarch64" ]; then
  MANYLINUX="manylinux_2_28_aarch64"
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi

docker run \
    -it \
    -v "$(pwd)":/io \
    -e PLAT="$MANYLINUX" \
    --rm \
    quay.io/pypa/"$MANYLINUX" \
    /io/accelerate/_build-manylinux.sh
