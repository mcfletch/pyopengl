"""Keeping the shallow checkout of the Khronos sources at their tip.

These drive real git against throwaway repositories: the checkout is a depth-1
clone, and what is being checked is how git updates one when upstream moves.
"""

import os
import subprocess

import pytest

from directdocs import acquireoriginal


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


def commit(repository, text, *flags):
    (repository / 'page.xml').write_text(text, encoding='utf-8')
    git('add', '-A', cwd=str(repository))
    git('commit', '-q', '-m', text, *flags, cwd=str(repository))


@pytest.fixture
def upstream(tmp_path):
    """A repository standing in for KhronosGroup/OpenGL-Refpages, two commits deep."""
    root = tmp_path / 'upstream'
    root.mkdir()
    git('init', '-q', '-b', 'main', '.', cwd=str(root))
    commit(root, 'first')
    commit(root, 'second')
    return root


@pytest.fixture
def checkout(tmp_path, upstream, monkeypatch):
    """The sources cloned from ``upstream`` the way a build clones them.

    A ``file://`` URL rather than a path, since git ignores ``--depth`` for a
    clone from a local path and the checkout would not be shallow.
    """
    directory = tmp_path / 'directdocs'
    directory.mkdir()
    monkeypatch.setattr(
        acquireoriginal,
        'MAN_SOURCES',
        [(upstream.as_uri(), 'OpenGL-Refpages')],
    )
    (target,) = acquireoriginal.ensure_sources(str(directory))
    assert git('rev-parse', '--is-shallow-repository', cwd=target) == 'true'
    return directory


def page(directory):
    return (directory / 'OpenGL-Refpages' / 'page.xml').read_text(encoding='utf-8')


class TestUpdating:
    def test_a_new_commit_upstream_is_checked_out(self, upstream, checkout):
        commit(upstream, 'third')
        acquireoriginal.ensure_sources(str(checkout))
        assert page(checkout) == 'third'

    def test_a_rewritten_tip_upstream_is_checked_out(self, upstream, checkout):
        commit(upstream, 'second, amended', '--amend')
        acquireoriginal.ensure_sources(str(checkout))
        assert page(checkout) == 'second, amended'

    def test_no_update_leaves_the_checkout_alone(self, upstream, checkout):
        commit(upstream, 'third')
        acquireoriginal.ensure_sources(str(checkout), update=False)
        assert page(checkout) == 'second'

    def test_a_local_edit_upstream_also_changes_is_kept(self, upstream, checkout):
        (checkout / 'OpenGL-Refpages' / 'page.xml').write_text(
            'edited here', encoding='utf-8'
        )
        commit(upstream, 'second, amended', '--amend')
        with pytest.raises(subprocess.CalledProcessError):
            acquireoriginal.ensure_sources(str(checkout))
        assert page(checkout) == 'edited here'
