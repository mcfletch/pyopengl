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
somewhere else to look at, and ``--publish`` commits it to the ``htdocs``
branch, which is what the site is served from.  Publishing writes through git's
plumbing rather than checking the branch out, so it never touches the working
tree; nothing leaves this machine until ``--push`` is given as well.

Run ``python build-docs.py --help`` for the rest.
"""

from __future__ import annotations

import argparse
import datetime
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

#: The branch the built site is served from.
PUBLISH_BRANCH = 'htdocs'

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


def publish(source: str, branch: str, message: str, push: str | None) -> str:
    """Commit the contents of ``source`` onto ``branch``.

    Through git's plumbing, with an index of its own: the branch is never
    checked out, so whatever is in the working tree stays exactly as it is.
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
    existing = subprocess.run(
        ['git', 'rev-parse', '--verify', '--quiet', 'refs/heads/%s' % (branch,)],
        capture_output=True,
        text=True,
        cwd=HERE,
    ).stdout.strip()
    if existing:
        if run(['git', 'rev-parse', '%s^{tree}' % (existing,)]).strip() == tree:
            log.info('%s already has this content; nothing to commit', branch)
            return existing
        parents = ['-p', existing]

    commit = run(['git', 'commit-tree', tree, '-m', message] + parents).strip()
    git('update-ref', 'refs/heads/%s' % (branch,), commit)
    log.info('%s is now %s', branch, commit[:12])

    if push:
        log.info('pushing %s to %s', branch, push)
        git('push', push, '%s:refs/heads/%s' % (branch, branch))
    return commit


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
        choices=['fetch', 'reference', 'api', 'html', 'none'],
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
        help='commit the built site to the %s branch' % (PUBLISH_BRANCH,),
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
        for step in (options.only or ['fetch', 'reference', 'api', 'html'])
        if step != 'none'
    ]
    if options.push and not options.publish:
        parser.error('--push publishes, so it needs --publish as well')

    try:
        if 'fetch' in steps:
            fetch(update=not options.no_fetch)
        if 'reference' in steps:
            build_reference(options.verbose)
        if 'api' in steps:
            build_api(options.skip, options.verbose)
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
            publish(options.output, options.branch, message, options.push)
    except Failed as err:
        log.error('%s', err)
        return 1
    except subprocess.CalledProcessError as err:
        log.error('%s exited %d', ' '.join(err.cmd), err.returncode)
        return err.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
