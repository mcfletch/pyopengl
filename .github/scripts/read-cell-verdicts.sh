#!/usr/bin/env bash
# Fail the run for a cell that reported a failure, and not for one that never
# reported.
#
#     read-cell-verdicts.sh <directory the cell artifacts were downloaded into>
#
# Each cell writes `verdict` into its test-log artifact, so a cell that ran
# leaves one and a cell that did not leaves nothing at all -- which is what a
# queued job cancelled at GitHub's twenty-four-hour limit leaves, and what a
# cell killed at its own `timeout-minutes` leaves. Neither is a statement about
# the library, so neither fails the run; a recorded failure is, and does.
#
# How many cells there should be comes from the cells themselves -- each
# records the matrix size it is one of -- so the count here cannot fall out of
# step with the matrix.

set -uo pipefail

root=${1:-cells}

shopt -s nullglob

reported=0
failed=0
total=0

for file in "$root"/*/verdict; do
    reported=$((reported + 1))
    cell=$(sed -n 's/^cell //p' "$file")
    said=$(sed -n 's/^verdict //p' "$file")
    count=$(sed -n 's/^total //p' "$file")

    case "$count" in
        ''|*[!0-9]*) ;;
        *) [ "$count" -gt "$total" ] && total=$count ;;
    esac

    printf '%s: %s\n' "${cell:-a cell that did not name itself}" "$said"
    sed -n 's/^area /    /p' "$file"

    [ "$said" = fail ] && failed=$((failed + 1))
done

if [ "$failed" -gt 0 ]; then
    echo "::error::$failed of the $reported cells that reported had a failing area"
    exit 1
fi

if [ "$reported" -eq 0 ]; then
    echo "::warning::no cell reported, so nothing was tested here"
    exit 0
fi

if [ "$total" -gt "$reported" ]; then
    echo "::warning::$((total - reported)) of the $total cells did not report;" \
         "each either never got a runner or ran out of time"
fi

echo "$reported of $total cells reported, and none had a failing area"
