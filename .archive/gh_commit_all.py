#!/usr/bin/env python3

import logging
import os
from pathlib import Path
from git import Repo


logger = logging.getLogger(__name__)


def commit_all(root_dir: Path, message: str = 'Posting Feedback'):

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


if __name__ == "__main__":

    import argparse

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    _base_logging_level = logging.WARNING

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(_base_logging_level)


    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.description = '''
    '''

    parser.add_argument("root_dir", type=dir_path, help="the directory containing the student repositories")
    parser.add_argument("message", type=str, nargs='?', help="message to apply to all commits (default='Feedback Posted')", default="Feedback Posted")
    parser.add_argument("-v", "--verbose", help="set to enable verbose output", action="store_true")
    parser.add_argument("-d", "--debug", help="set to enable debug output", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)

    root_dir = Path(os.path.abspath(args.root_dir))

    if not root_dir.is_dir():
        logger.error(f"{root_dir} is not a valid directory")
        exit(1)

    commit_all(root_dir, args.message)
