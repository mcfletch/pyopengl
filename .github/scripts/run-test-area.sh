#!/usr/bin/env bash
# Run one area of the suite, keep its whole output, and record what it said.
#
#     run-test-area.sh <area> <command> [argument ...]
#
# The record is a file beside the log rather than the step's own outcome,
# because that outcome is `failure` both for an area that failed and for a step
# GitHub killed at its `timeout-minutes` -- and those are different facts. A
# failure is a verdict on the library; a step that was killed stopped somewhere
# in the middle of a case and has no verdict in it at all.
#
# The status is written after the command has reported, so a killed step leaves
# a log and no status. That is how `record-test-areas.sh` tells one from the
# other.

set -uo pipefail

if [ "$#" -lt 2 ]; then
    echo "usage: $0 <area> <command> [argument ...]" >&2
    exit 2
fi

area=$1
shift

mkdir -p test-logs
"$@" 2>&1 | tee "test-logs/$area.log"
code=${PIPESTATUS[0]}

if [ "$code" -eq 0 ]; then
    printf 'pass\n' > "test-logs/$area.status"
else
    printf 'fail\n' > "test-logs/$area.status"
fi

exit "$code"
