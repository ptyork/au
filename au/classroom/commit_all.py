#!/usr/bin/env python3

import click

from pathlib import Path
from git import Repo

import logging
_base_logging_level = logging.INFO
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(_base_logging_level)

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

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)

    for student_dir in root_dir.iterdir():
        if not student_dir.is_dir():
            continue

        try:
            repo = Repo(student_dir)
        except:
            print(f"SKIPPING {student_dir}: is not a Git repository")
            continue

        if not repo.is_dirty(untracked_files=True):
            print(f"SKIPPING {student_dir}: no changes to commit")
            continue

        if preview:
            print(f"WOULD PROCESS {student_dir}")
            continue

        print(f"PROCESSING {student_dir}")

        try:
            logger.info(f"git pull")
            repo.git.pull()

            logger.info(f"git add .")
            repo.git.add('.')

            logger.info(f"git commit -m {message}")
            repo.git.commit(f'-m {message}')

            logger.info(f"git push")
            repo.git.push()
        except Exception as ex:
            logger.exception("Error occurred running git command")


if __name__ == '__main__':
    commit_all()
