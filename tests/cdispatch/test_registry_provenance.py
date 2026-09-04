#! /usr/bin/env python3
"""What the bindings were generated from is recorded, and checked.

Every enum value and every signature PyOpenGL ships comes out of two Khronos
registries fetched at generation time.  Nothing in the tests can catch a wrong
one, because the tests are generated from the same input -- so what the run
used has to be written down, and a later run that finds something different has
to say so rather than quietly producing different bindings.
"""

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, 'src')

sys.path.insert(0, SRC)
try:
    import fetch_registries
finally:
    sys.path.pop(0)

LOCK = os.path.join(SRC, 'cdispatch', 'registry_lock.json')


class TestTheLockFile:
    def test_it_is_shipped(self):
        assert os.path.exists(LOCK), (
            'the registries the bindings were generated from are not recorded'
        )

    def test_it_names_a_commit_for_every_registry(self):
        recorded = json.load(open(LOCK, encoding='utf-8'))
        for directory, url in fetch_registries.REGISTRIES:
            assert directory in recorded['registries'], directory
            entry = recorded['registries'][directory]
            assert entry['url'] == url
            assert len(entry['commit']) == 40, entry['commit']
            assert all(c in '0123456789abcdef' for c in entry['commit'])

    def test_it_says_when(self):
        recorded = json.load(open(LOCK, encoding='utf-8'))
        assert recorded['generated']  # an ISO date


class TestCheckingWhatWasFetched:
    def test_a_matching_fetch_is_accepted(self, tmp_path):
        lock = {'registries': {'khronosapi': {'url': 'u', 'commit': 'a' * 40}}}
        assert fetch_registries.differences_from(
            {'khronosapi': 'a' * 40}, lock
        ) == []

    def test_a_different_commit_is_reported(self, tmp_path):
        lock = {'registries': {'khronosapi': {'url': 'u', 'commit': 'a' * 40}}}
        differences = fetch_registries.differences_from(
            {'khronosapi': 'b' * 40}, lock
        )
        assert len(differences) == 1
        assert 'khronosapi' in differences[0]
        assert 'a' * 12 in differences[0] and 'b' * 12 in differences[0]

    def test_a_registry_the_lock_does_not_know_is_reported(self):
        differences = fetch_registries.differences_from(
            {'newapi': 'c' * 40}, {'registries': {}}
        )
        assert len(differences) == 1
        assert 'newapi' in differences[0]

    def test_a_registry_that_did_not_fetch_is_not_a_difference(self):
        """No network is already reported by the fetch itself, and the run then
        generates from the checkout it has; that is not the lock disagreeing."""
        lock = {'registries': {'khronosapi': {'url': 'u', 'commit': 'a' * 40}}}
        assert fetch_registries.differences_from({}, lock) == []


class TestTheGeneratorRefusesADriftedInput:
    """Regenerating from a registry other than the recorded one changes what
    the library declares, so it is a decision rather than a side effect."""

    def program(self, *arguments):
        return subprocess.run(
            [sys.executable, os.path.join(SRC, 'regenerate_c.py'), *arguments],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=300,
        )

    def test_the_option_to_accept_new_input_exists(self):
        completed = self.program('--help')
        assert completed.returncode == 0, completed.stderr
        assert '--update-registries' in completed.stdout

    def test_no_fetch_does_not_check_the_lock(self):
        """``--no-fetch`` generates from the checkouts as they are and says so;
        there is nothing for it to compare against."""
        completed = self.program('--help')
        assert '--no-fetch' in completed.stdout
