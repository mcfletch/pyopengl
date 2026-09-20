"""Putting the built site on the branch GitHub Pages serves.

Publishing force-pushes a branch, which is the one operation here that can
destroy something, so what it does is worth pinning down: it replaces the
branch rather than adding to it, it never touches the working tree, and it
refuses rather than overwrite a site somebody else published while this one
was building.

These drive the real thing against throwaway repositories, because what is
being checked is git's behaviour and not a description of it.
"""

import importlib.util
import os
import subprocess

import pytest

import paths

SCRIPT = os.path.join(paths.ROOT, 'build-docs.py')


@pytest.fixture(scope='module')
def build_docs():
    """``build-docs.py``, which is a script rather than a module."""
    spec = importlib.util.spec_from_file_location('build_docs', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*arguments, cwd, **kwargs):
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
        **kwargs,
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path, build_docs, monkeypatch):
    """A repository with one commit, which publishing will act on.

    ``build-docs.py`` runs git in its own directory, so that is pointed here
    rather than at the checkout this suite is running from -- a test that
    force-pushed the real `gh-pages` would be a test that published.
    """
    root = tmp_path / 'repo'
    root.mkdir()
    git('init', '-q', '-b', 'main', '.', cwd=str(root))
    (root / 'source.txt').write_text('the working tree', encoding='utf-8')
    git('add', '-A', cwd=str(root))
    git('commit', '-q', '-m', 'first', cwd=str(root))
    monkeypatch.setattr(build_docs, 'HERE', str(root))
    return root


@pytest.fixture
def remote(tmp_path, repository):
    """A bare repository standing in for the one on GitHub."""
    path = tmp_path / 'remote.git'
    git('init', '-q', '--bare', str(path), cwd=str(tmp_path))
    git('remote', 'add', 'origin', str(path), cwd=str(repository))
    return path


def site(tmp_path, name, text):
    """A directory shaped like a built documentation set."""
    directory = tmp_path / name
    (directory / '_static').mkdir(parents=True)
    (directory / 'index.html').write_text(text, encoding='utf-8')
    (directory / '_static' / 'style.css').write_text('a{}', encoding='utf-8')
    return str(directory)


def parents_of(repo, ref):
    return git('log', '-1', '--format=%P', ref, cwd=str(repo)).split()


def commits_in(repo, ref):
    return int(git('rev-list', '--count', ref, cwd=str(repo)))


def content_of(repo, ref, path):
    return git('show', '%s:%s' % (ref, path), cwd=str(repo))


class TestTheShapeOfAPublish:
    def test_the_first_publish_is_a_root_commit(self, build_docs, repository, tmp_path):
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        assert parents_of(repository, 'gh-pages') == []
        assert commits_in(repository, 'gh-pages') == 1

    def test_a_second_publish_replaces_rather_than_adds(
        self, build_docs, repository, tmp_path
    ):
        """One copy of the site in the repository, however many releases."""
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        build_docs.publish(site(tmp_path, 'two', 'second'), 'gh-pages', 'two', None)
        assert commits_in(repository, 'gh-pages') == 1
        assert parents_of(repository, 'gh-pages') == []
        assert content_of(repository, 'gh-pages', 'index.html') == 'second'

    def test_keep_history_chains_instead(self, build_docs, repository, tmp_path):
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        build_docs.publish(
            site(tmp_path, 'two', 'second'),
            'gh-pages',
            'two',
            None,
            keep_history=True,
        )
        assert commits_in(repository, 'gh-pages') == 2

    def test_a_nojekyll_marker_goes_with_it(self, build_docs, repository, tmp_path):
        """Without it Pages runs Jekyll, which drops `_static`."""
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        listing = git(
            'ls-tree', '-r', '--name-only', 'gh-pages', cwd=str(repository)
        ).split()
        assert '.nojekyll' in listing
        assert '_static/style.css' in listing

    def test_the_working_tree_is_untouched(self, build_docs, repository, tmp_path):
        """The branch is never checked out, so nothing in the checkout moves."""
        before = git('status', '--porcelain', cwd=str(repository))
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        assert git('status', '--porcelain', cwd=str(repository)) == before
        assert (repository / 'source.txt').read_text(encoding='utf-8') == (
            'the working tree'
        )
        assert git('rev-parse', '--abbrev-ref', 'HEAD', cwd=str(repository)) == 'main'

    def test_rebuilding_the_same_sources_commits_nothing_new(
        self, build_docs, repository, tmp_path
    ):
        first = build_docs.publish(
            site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None
        )
        again = build_docs.publish(
            site(tmp_path, 'again', 'first'), 'gh-pages', 'one again', None
        )
        assert first == again

    def test_publishing_nothing_is_refused(self, build_docs, repository, tmp_path):
        with pytest.raises(build_docs.Failed) as raised:
            build_docs.publish(str(tmp_path / 'absent'), 'gh-pages', 'x', None)
        assert 'does not exist' in str(raised.value)


class TestPushing:
    def test_the_first_push_creates_the_branch(
        self, build_docs, repository, remote, tmp_path
    ):
        build_docs.publish(
            site(tmp_path, 'one', 'first'), 'gh-pages', 'one', 'origin', lease=''
        )
        assert content_of(remote, 'gh-pages', 'index.html') == 'first'
        assert commits_in(remote, 'gh-pages') == 1

    def test_the_next_push_replaces_the_branch(
        self, build_docs, repository, remote, tmp_path
    ):
        build_docs.publish(
            site(tmp_path, 'one', 'first'), 'gh-pages', 'one', 'origin', lease=''
        )
        was = git('rev-parse', 'gh-pages', cwd=str(repository))
        build_docs.publish(
            site(tmp_path, 'two', 'second'), 'gh-pages', 'two', 'origin', lease=was
        )
        assert content_of(remote, 'gh-pages', 'index.html') == 'second'
        assert commits_in(remote, 'gh-pages') == 1
        assert parents_of(remote, 'gh-pages') == []

    def test_a_push_that_failed_is_retried_by_publishing_again(
        self, build_docs, repository, remote, tmp_path
    ):
        """The branch being right here says nothing about the remote."""
        build_docs.publish(site(tmp_path, 'one', 'first'), 'gh-pages', 'one', None)
        build_docs.publish(
            site(tmp_path, 'again', 'first'), 'gh-pages', 'one', 'origin', lease=''
        )
        assert content_of(remote, 'gh-pages', 'index.html') == 'first'

    def test_a_site_published_in_between_is_not_replaced(
        self, build_docs, repository, remote, tmp_path
    ):
        """The lease is where the remote was when the build started.  Somebody
        else publishing during those ten minutes has to be a refusal, or their
        site is gone and nothing says so."""
        build_docs.publish(
            site(tmp_path, 'one', 'first'), 'gh-pages', 'one', 'origin', lease=''
        )
        stale = git('rev-parse', 'gh-pages', cwd=str(repository))

        elsewhere = tmp_path / 'elsewhere'
        git('clone', '-q', '-b', 'gh-pages', str(remote), str(elsewhere), cwd=str(tmp_path))
        (elsewhere / 'index.html').write_text('somebody else', encoding='utf-8')
        git('add', '-A', cwd=str(elsewhere))
        git('commit', '-q', '-m', 'elsewhere', cwd=str(elsewhere))
        git('push', '-q', 'origin', 'gh-pages', cwd=str(elsewhere))

        with pytest.raises(build_docs.Failed) as raised:
            build_docs.publish(
                site(tmp_path, 'two', 'second'),
                'gh-pages',
                'two',
                'origin',
                lease=stale,
            )
        assert 'something else published' in str(raised.value)
        assert content_of(remote, 'gh-pages', 'index.html') == 'somebody else'


class TestTheDefaults:
    def test_the_branch_is_the_one_github_pages_serves(self, build_docs):
        assert build_docs.PUBLISH_BRANCH == 'gh-pages'
