#!/bin/bash
set -e -u -x
# Build manylinux compatible wheel files using docker...

DIRECTORY=/io/accelerate
DIST=${DIRECTORY}/manylinux-dist

function repair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$PLAT" -w ${DIST}
    fi
}


# Install a system package required by our library
# yum install -y atlas-devel

# Compile wheels
cd ${DIRECTORY}

for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -r ${DIRECTORY}/dev-requirements.txt
    PIP_PLATFORM=${PLAT} "${PYBIN}/pip" wheel ${DIRECTORY} --no-deps -w ${DIST}
done

# Bundle external shared libraries into the wheels
for whl in ${DIST}/*.whl; do
    repair_wheel "$whl"
done
