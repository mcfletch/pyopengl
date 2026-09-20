#! /usr/bin/env python3
"""Builds the PyOpenGL documentation set, and publishes it.

The set has three parts:

``docs/*.rst``
    written by hand.

``docs/reference/``
    the OpenGL reference pages with PyOpenGL's call signatures added, written
    by ``directdocs/generate.py`` from the Khronos DocBook sources.

``docs/api/``
    a page per Python module, written by ``directdocs/dumbpydoc.py`` from the
    installed packages.

The two generated directories are not in version control, so a plain run makes
everything::

    python build-docs.py

and leaves the site in ``docs/_build/html``.  ``--stage DIR`` puts a copy
somewhere else to look at, and ``--publish`` puts it on ``gh-pages``, which is
what GitHub Pages serves.

Publishing writes through git's plumbing rather than checking the branch out,
so it never touches the working tree, and it replaces the branch with a single
commit that has no parent.  The repository therefore carries one copy of the
site rather than one per release: a hundred megabytes of HTML that packs to
eight, which would otherwise grow by a few megabytes every time a release
changed the version line on every page.  ``--push`` forces the branch over,
against a lease so that a publish from elsewhere is refused rather than lost;
nothing leaves this machine without it.

Run ``python build-docs.py --help`` for the rest.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import logging
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, 'docs')
REFERENCE = os.path.join(DOCS, 'reference')
API = os.path.join(DOCS, 'api')
HTML = os.path.join(DOCS, '_build', 'html')
DOCTREES = os.path.join(DOCS, '_build', 'doctrees')

#: The branch GitHub Pages serves the site from.
PUBLISH_BRANCH = 'gh-pages'

log = logging.getLogger('build-docs')


class Failed(Exception):
    """A step did not succeed; the message says which and why."""


def run(command: list[str], **kwargs) -> str:
    """Run ``command``, returning its output and raising on a non-zero exit."""
    log.debug('$ %s', ' '.join(command))
    result = subprocess.run(
        command, capture_output=True, text=True, cwd=kwargs.pop('cwd', HERE), **kwargs
    )
    if result.returncode:
        raise Failed(
            '%s exited %d\n%s%s'
            % (' '.join(command), result.returncode, result.stdout, result.stderr)
        )
    return result.stdout


def git(*arguments: str, **kwargs) -> str:
    return run(['git'] + list(arguments), **kwargs)


# ----------------------------------------------------------------------
# the three generation steps


def fetch(update: bool) -> None:
    """Make sure the Khronos DocBook sources are present."""
    sys.path.insert(0, HERE)
    from directdocs import acquireoriginal

    acquireoriginal.ensure_sources(update=update)


def build_reference(verbose: bool) -> None:
    log.info('Writing the reference pages into %s', REFERENCE)
    shutil.rmtree(REFERENCE, ignore_errors=True)
    command = [sys.executable, os.path.join(HERE, 'directdocs', 'generate.py')]
    if verbose:
        command.append('--verbose')
    subprocess.check_call(command, cwd=os.path.join(HERE, 'directdocs'))


def build_api(skip: list[str], verbose: bool) -> None:
    log.info('Writing the API pages into %s', API)
    shutil.rmtree(API, ignore_errors=True)
    command = [sys.executable, os.path.join(HERE, 'directdocs', 'dumbpydoc.py')]
    for name in skip:
        command.extend(['--skip', name])
    if verbose:
        command.append('--verbose')
    subprocess.check_call(command, cwd=HERE)


#: The prose reviewer, if this checkout sits in the workspace that carries it.
#: `.claude/skills/ai-isms` is a workspace-level skill rather than part of this
#: repository, so a CI run building the docs from a clone has none and the step
#: says so instead of failing.
AI_ISMS = os.path.join(
    '.claude', 'skills', 'ai-isms', 'scripts', 'scan.py'
)


def prose_scanner() -> str | None:
    """Where the prose scanner is, or None where this checkout has no reach to one.

    ``AI_ISMS_SCAN`` names it directly; otherwise the directories above this
    one are searched, which is what finds the workspace copy from a submodule.
    """
    named = os.environ.get('AI_ISMS_SCAN')
    if named:
        return named if os.path.isfile(named) else None
    directory = HERE
    while True:
        candidate = os.path.join(directory, AI_ISMS)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def check_prose() -> None:
    """Report the marks of machine-written prose in the hand-written pages.

    Reported rather than enforced: every match is a question about a particular
    sentence, and a build is not where that is answered.  The generated
    directories are left out -- their prose is Khronos's, and the fix to
    anything in them is to the generator.
    """
    scanner = prose_scanner()
    if scanner is None:
        log.info('No prose scanner found; skipping the prose pass')
        return
    pages = sorted(glob.glob(os.path.join(DOCS, '*.rst')))
    log.info('Reading %d hand-written pages for the marks of generated prose', len(pages))
    subprocess.call(
        [sys.executable, '-W', 'ignore::SyntaxWarning', scanner, '--all']
        + pages,
        cwd=HERE,
    )


def build_html(output: str, builder: str, warnings_are_errors: bool) -> None:
    log.info('Building %s into %s', builder, output)
    command = [
        sys.executable,
        '-m',
        'sphinx',
        '-b',
        builder,
        '-j',
        'auto',
        '-d',
        DOCTREES,
    ]
    if warnings_are_errors:
        command.append('-W')
    command.extend([DOCS, output])
    subprocess.check_call(command, cwd=HERE)
    nojekyll(output)


def nojekyll(directory: str) -> None:
    """Put a ``.nojekyll`` marker in ``directory``.

    GitHub Pages runs Jekyll over a branch unless told not to, and Jekyll drops
    every directory whose name starts with an underscore -- which is
    ``_static``, so the site would come out with no stylesheet and no search.
    """
    open(os.path.join(directory, '.nojekyll'), 'w').close()


# ----------------------------------------------------------------------
# publishing


def publish(
    source: str,
    branch: str,
    message: str,
    push: str | None,
    keep_history: bool = False,
    lease: str | None = None,
) -> str:
    """Commit the contents of ``source`` onto ``branch``.

    Through git's plumbing, with an index of its own: the branch is never
    checked out, so whatever is in the working tree stays exactly as it is.

    The commit has no parent.  Each publish replaces the branch with a single
    disjoint commit rather than adding to a chain, so the repository carries
    one generation of the site rather than one per release.  The site is about
    a hundred megabytes of HTML that packs to eight, and a release changes a
    line on every page, so a kept history costs a few megabytes a release --
    which is nothing for a while and not nothing for a decade.  ``--push``
    then has to force, and does it with a lease, so a publish from somewhere
    else is a refusal rather than a loss.

    ``keep_history`` chains onto the previous commit instead, for a branch
    where the trail is wanted more than the size.

    Returns the new commit.
    """
    if not os.path.isdir(source):
        raise Failed('nothing to publish: %s does not exist' % (source,))
    nojekyll(source)
    git_dir = run(['git', 'rev-parse', '--absolute-git-dir']).strip()

    with tempfile.TemporaryDirectory(prefix='pyopengl-docs-') as scratch:
        environment = dict(os.environ, GIT_INDEX_FILE=os.path.join(scratch, 'index'))
        # -f because the repository's own .gitignore has no say over a tree of
        # built files, and an ignored name there would silently go missing.
        run(
            [
                'git',
                '--git-dir=%s' % (git_dir,),
                '--work-tree=%s' % (os.path.abspath(source),),
                'add',
                '-A',
                '-f',
                '.',
            ],
            cwd=source,
            env=environment,
        )
        tree = run(
            ['git', '--git-dir=%s' % (git_dir,), 'write-tree'], env=environment
        ).strip()

    parents = []
    existing = local_head(branch)
    unchanged = bool(existing) and (
        run(['git', 'rev-parse', '%s^{tree}' % (existing,)]).strip() == tree
    )
    if unchanged:
        # A rebuild of the same sources.  Recommitting it would make a commit
        # that says nothing; the push below still happens, because the branch
        # being right here says nothing about whether it is right on the
        # remote -- a push that failed last time is exactly when this runs
        # again.
        log.info('%s already has this content, at %s', branch, existing[:12])
        commit = existing
    else:
        if existing and keep_history:
            parents = ['-p', existing]
        commit = run(['git', 'commit-tree', tree, '-m', message] + parents).strip()
        git('update-ref', 'refs/heads/%s' % (branch,), commit)
        log.info(
            '%s is now %s (%s)',
            branch,
            commit[:12],
            'on the previous commit' if parents else 'a new root commit',
        )

    if push:
        push_branch(branch, push, forced=not parents, lease=lease)
    return commit


def local_head(branch: str) -> str:
    """The commit ``branch`` is at here, or ``''`` if there is no such branch."""
    return subprocess.run(
        ['git', 'rev-parse', '--verify', '--quiet', 'refs/heads/%s' % (branch,)],
        capture_output=True,
        text=True,
        cwd=HERE,
    ).stdout.strip()


def remote_head(remote: str, branch: str) -> str:
    """The commit ``branch`` is at on ``remote``, or ``''`` if it has none."""
    output = run(['git', 'ls-remote', remote, 'refs/heads/%s' % (branch,)])
    return output.split()[0] if output.strip() else ''


def push_branch(
    branch: str, remote: str, forced: bool, lease: str | None = None
) -> None:
    """Send ``branch`` to ``remote``, forcing it only over what was there.

    A disjoint commit shares no history with what the remote has, so the push
    has to be forced.  Forced against a lease rather than outright, and the
    lease is where the remote was when this run *started* -- read before the
    build rather than after it, because the build is the ten minutes during
    which somebody else could publish.  A lease read at push time would name
    their commit and replace it, which is the thing worth not doing.

    An empty lease means the branch was not there at all, which git reads as
    "and must still not be".
    """
    refspec = '%s:refs/heads/%s' % (branch, branch)
    if not forced:
        log.info('pushing %s to %s', branch, remote)
        git('push', remote, refspec)
        return
    if lease is None:
        lease = remote_head(remote, branch)
    log.info(
        'replacing %s on %s (%s)',
        branch,
        remote,
        'was %s' % (lease[:12],) if lease else 'which did not have it',
    )
    try:
        git(
            'push',
            '--force-with-lease=refs/heads/%s:%s' % (branch, lease),
            remote,
            refspec,
        )
    except Failed as err:
        raise Failed(
            '%s on %s is not %s any more, so this did not replace it: '
            'something else published while this was building. Look at what '
            'is there, then build and publish again.\n%s'
            % (branch, remote, lease[:12] if lease else '(absent)', err)
        ) from err


def stage(source: str, target: str) -> None:
    """Put a copy of the built site where somebody can look at it."""
    target = os.path.abspath(target)
    if os.path.exists(target):
        if not os.path.isdir(target):
            raise Failed('%s exists and is not a directory' % (target,))
        shutil.rmtree(target)
    shutil.copytree(source, target)
    log.info('Staged the site in %s', target)


# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split('\n')[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Without --only, everything is regenerated and rebuilt.',
    )
    parser.add_argument(
        '--only',
        action='append',
        choices=['fetch', 'reference', 'api', 'prose', 'html', 'none'],
        default=[],
        help=(
            'run just this step; may be given more than once.  "none" builds '
            'nothing, which is what to give with --stage or --publish to send '
            'out a site that is already built'
        ),
    )
    parser.add_argument(
        '--no-fetch',
        action='store_true',
        help='use the DocBook sources already checked out rather than pulling',
    )
    parser.add_argument(
        '--skip',
        action='append',
        default=[],
        metavar='MODULE',
        help=(
            'leave a module and everything under it out of the API pages; '
            '"--skip OpenGL.raw" halves the page count for a quick look'
        ),
    )
    parser.add_argument(
        '--output',
        default=HTML,
        help='where the built site goes (default: %(default)s)',
    )
    parser.add_argument(
        '--builder', default='html', help='Sphinx builder (default: %(default)s)'
    )
    parser.add_argument(
        '-W',
        '--warnings-are-errors',
        action='store_true',
        help='fail the build on any Sphinx warning',
    )
    parser.add_argument(
        '--stage',
        metavar='DIR',
        help='also copy the built site to DIR, replacing what is there',
    )
    parser.add_argument(
        '--publish',
        action='store_true',
        help=(
            'replace the %s branch with the built site, as a single commit '
            'with no parent' % (PUBLISH_BRANCH,)
        ),
    )
    parser.add_argument(
        '--keep-history',
        action='store_true',
        help=(
            'add to the published branch rather than replacing it, keeping '
            'every release in its history at a few megabytes each'
        ),
    )
    parser.add_argument(
        '--branch',
        default=PUBLISH_BRANCH,
        help='branch to publish to (default: %(default)s)',
    )
    parser.add_argument(
        '--push',
        nargs='?',
        const='origin',
        metavar='REMOTE',
        help='push the published branch to REMOTE (default: origin)',
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='say what each step is doing'
    )
    options = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.INFO,
        format='%(message)s',
    )

    steps = [
        step
        for step in (options.only or ['fetch', 'reference', 'api', 'prose', 'html'])
        if step != 'none'
    ]
    if options.push and not options.publish:
        parser.error('--push publishes, so it needs --publish as well')

    # Read before anything is built.  The build takes about ten minutes, and
    # this is what a publish landing during them is detected against.
    lease = None
    if options.publish and options.push:
        lease = remote_head(options.push, options.branch)

    try:
        if 'fetch' in steps:
            fetch(update=not options.no_fetch)
        if 'reference' in steps:
            build_reference(options.verbose)
        if 'api' in steps:
            build_api(options.skip, options.verbose)
        if 'prose' in steps:
            check_prose()
        if 'html' in steps:
            build_html(
                options.output, options.builder, options.warnings_are_errors
            )
        if options.stage:
            stage(options.output, options.stage)
        if options.publish:
            message = 'Documentation built %s' % (
                datetime.datetime.now().isoformat(timespec='seconds'),
            )
            publish(
                options.output,
                options.branch,
                message,
                options.push,
                keep_history=options.keep_history,
                lease=lease,
            )
    except Failed as err:
        log.error('%s', err)
        return 1
    except subprocess.CalledProcessError as err:
        log.error('%s exited %d', ' '.join(err.cmd), err.returncode)
        return err.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
