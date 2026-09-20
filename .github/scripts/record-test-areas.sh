#!/usr/bin/env bash
# Say what each area of the suite reported, and write the cell's verdict.
#
#     CELL='macOS macos-14 / ...' TOTAL=6 record-test-areas.sh <area> [area ...]
#
# `CELL` is what to call this cell of the matrix and `TOTAL` is how many cells
# the matrix has; the workflow supplies both. The verdict goes into
# `test-logs/verdict`, which rides along in the cell's test-log artifact and is
# the only thing `read-cell-verdicts.sh` reads.
#
# An area falls into one of three states, and the run turns on which:
#
#   pass/fail   it ran and reported, and a fail is a verdict on the library
#   unfinished  it started and was killed at the step's limit
#   skipped     it never started, which a dispatch naming one path does
#
# Only a `fail` fails the run. An area that did not finish is a job that ran
# out of time rather than a library that misbehaved, so it is a warning here
# and in the run's annotations, and the log it did write is in the artifact.

set -uo pipefail

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <area> [area ...]" >&2
    exit 2
fi

mkdir -p test-logs

verdict=pass
areas=()

for area in "$@"; do
    if [ -f "test-logs/$area.status" ]; then
        said=$(cat "test-logs/$area.status")
    elif [ -f "test-logs/$area.log" ]; then
        said=unfinished
    else
        said=skipped
    fi

    case "$said" in
        fail)
            verdict=fail
            echo "::error::$area reported a failure"
            ;;
        unfinished)
            echo "::warning::$area was killed at the step's limit, so it" \
                 "reported nothing; its log up to that point is in the artifact"
            ;;
    esac

    printf '%-12s %s\n' "$area" "$said"
    areas+=("area $area $said")
done

{
    printf 'cell %s\n' "${CELL:-unnamed}"
    printf 'total %s\n' "${TOTAL:-0}"
    printf 'verdict %s\n' "$verdict"
    printf '%s\n' "${areas[@]}"
} > test-logs/verdict

[ "$verdict" = pass ]
