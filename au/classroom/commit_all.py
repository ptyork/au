#!/usr/bin/env python3

import click
from yaspin import yaspin

from pathlib import Path
from textwrap import fill

from au.lib.common.terminal import get_term_width
from au.lib.f_table.f_table import BasicScreenStyle, get_table
from au.lib.git import get_dirty_repos

import logging
logger = logging.getLogger(__name__)

@click.command()
@click.argument("root_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("-m", "--message", prompt=True, type=str, default="Posting feedback",
              help="The message to apply to all `git commit` calls")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
@click.option("-p", "--preview", is_flag=True, help="set to show changes without actually making them")
def commit_all(root_dir: Path,
               message: str = 'Posting feedback',
               debug: bool = False,
               quiet: bool = False,
               preview: bool = False):
    '''
    Commit all "dirty" repository subdirectories below a specified directory

    \b
    Required Argument:
      ROOT_DIR
        the base directory containing the files subdirectories to be committed

    Iterate over all immediate subdirectories of ROOT-DIR. If it is found to be
    a Git repository and if it contains changes, then:

    \b
        + add all changes
        + commit using --message
        + push all changes to the remote

    If the --message argument is not provided, the script will prompt for one.
    '''
    logging.basicConfig()

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.INFO)

    skips = []
    commits = []
    errors = []

    with yaspin().aesthetic as spinner:
        spinner.text="Finding repositories to commit"
        for repo in get_dirty_repositories(root_dir):
            if repo.name.startswith('_'):
                skips.append([repo.name, 'special directory'])
                continue

            if preview:
                commits.add([repo.name, "WOULD COMMIT"])
                continue

            try:
                spinner.text = f"{repo.name}: git pull"
                repo.git.pull()

                spinner.text = f"{repo.name}: git add ."
                repo.add()

                spinner.text = f"{repo.name}: git commit -m {message}"
                repo.commit(message)

                spinner.text = f"{repo.name}: git push"
                repo.push()

                commits.append([repo.name, "COMMITTED"])
            except Exception as ex:
                logger.exception("Error occurred running git command")
                errors.append([repo.name, str(ex)])

    # Print a summary
    if quiet:
        all_dirs = errors
    else:
        all_dirs = commits + skips + errors
    all_dirs.sort()

    print(get_table(all_dirs, col_defs=['','A'], style=BasicScreenStyle()))

    for dir in all_dirs:
        print(f' *  {dir[0].name}')
        print(fill(dir[1], get_term_width(), initial_indent='    '))

    print()

    summary = []
    summary.append([f'Rood Directory', root_dir])
    if preview:
        summary.append([f'Repositories to Commit', len(commits)])
    else:
        summary.append([f'Repositories Pushed', len(commits)])
    summary.append([f'Directories Skipped', len(skips)])
    summary.append([f'Errors Encountered', len(errors)])
    print(get_table(summary), style=BasicScreenStyle())

if __name__ == '__main__':
    commit_all()
