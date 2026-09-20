#! /usr/bin/env python3
"""A job that never finished is not a job that failed.

Three of the runners here are machines nobody on the project can log into, and
two of the ways a run of them ends say nothing about the library:

* GitHub holds a job that no runner has picked up for twenty-four hours and
  then cancels it.  ``timeout-minutes`` does not start until a runner takes the
  job, so it bounds none of that wait: a label with no free runner is a red
  suite a day later, about nothing.  ``macos-13`` is that label -- it is the
  only Intel Mac GitHub offers, and #139 is an Intel-Mac segfault, so the row
  stays and what it costs when it does not run is bounded here instead.
* A step killed at its own limit reports a number, not a failure.  Whatever it
  was running stopped mid-case, so there is no verdict to read out of it.

So a macOS cell records what each area of the suite reported, and the gate job
reads those records: a recorded failure fails the run, and a cell that never
reported does not.  That only holds while the workflow keeps the shape it
depends on, which is what this asserts:

* every job is bounded, since an unbounded one runs to GitHub's six-hour limit;
* every step whose failure is tolerated is bounded too, because a hang there
  spends the whole job on one area and the areas after it never run;
* a step that runs an area is given longer than ``pytest-timeout`` takes to
  report a hung case, so a single stuck test arrives as a failing test with a
  traceback rather than as a step that stopped saying nothing;
* and a job whose failure does not fail the run is read by some other job,
  because a failure nothing reads is a failure nobody sees.

The workflow is read with a regular expression rather than a YAML parser, for
the reason ``test_declared_gates_run.py`` gives: a YAML library in the ``test``
extra would be installed in all thirty matrix environments to read a few lines.
"""

import math
import os
import re

import paths
import pytest

WORKFLOW = os.path.join(paths.ROOT, '.github', 'workflows', 'test.yml')
PYPROJECT = os.path.join(paths.ROOT, 'pyproject.toml')

#: A job identifier: two spaces, a name, a colon, nothing else on the line.
JOB = re.compile(r'^  ([A-Za-z0-9_-]+):[ \t]*$', re.M)

#: Where a step begins: six spaces and a dash, so its own keys are at eight.
STEP = re.compile(r'^      - ', re.M)

#: The script a step runs an area of the suite through.
AREA_RUNNER = 'run-test-area.sh'


def _text(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def jobs():
    """``{name: the text of the job}`` for the workflow's jobs."""
    text = _text(WORKFLOW)
    head, _, body = text.partition('\njobs:\n')
    assert body, 'test.yml declares no jobs'
    found = {}
    starts = list(JOB.finditer(body))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        found[match.group(1)] = body[match.start():end]
    return found


def steps(job):
    """The text of each step in a job, the leading dash included."""
    return STEP.split(job)[1:]


def said(block):
    """``block`` without its comment lines, which declare and run nothing.

    The comments here are long, and several of them name the scripts and the
    keys the rules below look for -- so a rule reading the text as it stands
    would find a step in a paragraph about one.
    """
    return '\n'.join(
        line for line in block.splitlines() if not line.lstrip().startswith('#')
    )


def key(block, name, indent):
    """The value of ``name:`` at ``indent`` spaces in ``block``, or ``None``."""
    match = re.search(
        r'^%s%s:[ \t]*(.*)$' % (' ' * indent, re.escape(name)), said(block), re.M
    )
    return match.group(1).strip() if match else None


def step_name(step):
    """What a step calls itself, for naming it in a failure."""
    match = re.match(r'(?:name|uses):[ \t]*(.*)', step)
    return match.group(1).strip() if match else step.split('\n', 1)[0]


def area_jobs():
    """The jobs that run an area of the suite through the runner script."""
    return {
        name for name, job in jobs().items()
        if any(AREA_RUNNER in said(step) for step in steps(job))
    }


def needed():
    """Every job named in another job's ``needs``."""
    found = set()
    for job in jobs().values():
        declared = key(job, 'needs', 4)
        if declared:
            found |= set(re.findall(r'[A-Za-z0-9_-]+', declared))
    return found


def per_test_timeout_minutes():
    """``pytest-timeout``'s per-case bound, in whole minutes, rounded up."""
    match = re.search(r'^timeout\s*=\s*(\d+)\s*$', _text(PYPROJECT), re.M)
    assert match, 'pyproject.toml declares no per-test timeout'
    return math.ceil(int(match.group(1)) / 60)


class TestEveryRunIsBounded:
    @pytest.mark.parametrize('name', sorted(jobs()))
    def test_every_job_declares_a_timeout(self, name):
        assert key(jobs()[name], 'timeout-minutes', 4), (
            'job %r declares no timeout-minutes, so it runs to GitHub\'s own '
            'six-hour limit before anything cancels it' % (name,)
        )

    @pytest.mark.parametrize('name', sorted(jobs()))
    def test_a_tolerated_step_is_bounded(self, name):
        for step in steps(jobs()[name]):
            if key(step, 'continue-on-error', 8) != 'true':
                continue
            assert key(step, 'timeout-minutes', 8), (
                'step %r of job %r is allowed to fail but is not bounded, so a '
                'hang in it spends the whole job and the steps after it never '
                'run' % (step_name(step), name)
            )

    @pytest.mark.parametrize('name', sorted(jobs()))
    def test_an_area_gets_longer_than_a_hung_case_takes_to_report(self, name):
        floor = per_test_timeout_minutes() + 1
        for step in steps(jobs()[name]):
            if AREA_RUNNER not in said(step):
                continue
            bound = int(key(step, 'timeout-minutes', 8))
            assert bound >= floor, (
                'step %r of job %r is bounded at %d minutes, under the %d a '
                'hung case takes to be reported as a failing test -- so the '
                'step would be killed first, and the hang would arrive as an '
                'area that said nothing' % (step_name(step), name, bound, floor)
            )


class TestNothingToleratedGoesUnread:
    def test_a_job_that_cannot_fail_the_run_is_read_by_another(self):
        readers = needed()
        for name, job in jobs().items():
            if key(job, 'continue-on-error', 4) != 'true':
                continue
            assert name in readers, (
                'job %r cannot fail the run and no other job needs it, so a '
                'test that failed there fails nothing' % (name,)
            )

    def test_an_area_that_reported_a_failure_still_fails_the_run(self):
        """The three rules above are about a cell that says nothing.

        This is the other half, and the one that keeps them from amounting to
        a matrix nothing reads: a cell that is allowed not to finish has a gate
        job that reads what it did report.
        """
        readers = needed()
        for name in area_jobs():
            assert key(jobs()[name], 'continue-on-error', 4) == 'true', (
                'job %r runs areas that are each allowed to be killed at their '
                'own limit, so a cell that runs out of time fails the job -- '
                'and the job has to be the one thing that does not fail the '
                'run' % (name,)
            )
            assert name in readers, (
                'job %r records what each area reported and nothing reads the '
                'record, so a failing area fails nothing' % (name,)
            )


class TestTheseRulesHaveSomethingToSay:
    """A gate nothing runs stops being true -- so each rule names its subject.

    Every rule above is written over whatever the workflow happens to declare,
    which is what keeps them from going stale as jobs come and go.  It is also
    how all three would pass on a workflow that had quietly stopped running
    areas at all, so the subjects are asserted to exist.
    """

    def test_some_job_runs_an_area_through_the_runner(self):
        assert area_jobs(), (
            'no job runs %s, so the rules about an area that did not finish '
            'are about nothing' % (AREA_RUNNER,)
        )

    def test_some_step_is_allowed_to_fail(self):
        tolerated = [
            step_name(step)
            for job in jobs().values()
            for step in steps(job)
            if key(step, 'continue-on-error', 8) == 'true'
        ]
        assert tolerated, (
            'no step is allowed to fail, so the rule that a tolerated step is '
            'bounded is about nothing'
        )
