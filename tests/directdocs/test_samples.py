"""Keeping the sample checkouts on the branch the reference links point at.

These drive real git against throwaway repositories.
"""

import os
import subprocess

import pytest

from directdocs import samples


def git(*arguments, cwd):
    return subprocess.run(
        ['git'] + list(arguments),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=dict(
            os.environ,
            GIT_AUTHOR_NAME='t',
            GIT_AUTHOR_EMAIL='t@example.com',
            GIT_COMMITTER_NAME='t',
            GIT_COMMITTER_EMAIL='t@example.com',
        ),
    ).stdout.strip()


def commit(repository, text):
    (repository / 'sample.py').write_text(text, encoding='utf-8')
    git('add', '-A', cwd=str(repository))
    git('commit', '-q', '-m', text, cwd=str(repository))


@pytest.fixture
def upstream(tmp_path):
    """A project whose work moved from ``master`` to ``main``."""
    root = tmp_path / 'upstream'
    root.mkdir()
    git('init', '-q', '-b', 'master', '.', cwd=str(root))
    commit(root, 'on master')
    git('checkout', '-q', '-b', 'main', cwd=str(root))
    commit(root, 'on main')
    git('checkout', '-q', 'master', cwd=str(root))
    return root


def sample(directory):
    return (directory / 'project' / 'sample.py').read_text(encoding='utf-8')


class TestABranch:
    def test_a_new_checkout_is_on_it(self, upstream, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        samples.GITSource(upstream.as_uri(), 'project', branch='main').update()
        assert sample(tmp_path) == 'on main'

    def test_a_checkout_on_another_branch_moves_to_it(
        self, upstream, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        samples.GITSource(upstream.as_uri(), 'project').update()
        assert sample(tmp_path) == 'on master'
        samples.GITSource(upstream.as_uri(), 'project', branch='main').update()
        assert sample(tmp_path) == 'on main'

    def test_new_commits_on_it_arrive(self, upstream, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        source = samples.GITSource(upstream.as_uri(), 'project', branch='main')
        source.update()
        git('checkout', '-q', 'main', cwd=str(upstream))
        commit(upstream, 'later on main')
        source.update()
        assert sample(tmp_path) == 'later on main'


class TestTheCheckouts:
    def test_openglcontext_follows_main(self):
        """The reference links name ``blob/main``; ``master`` is years old."""
        (source,) = [s for s in samples.checkouts if s.dirname == 'OpenGLContext']
        assert source.branch == 'main'
