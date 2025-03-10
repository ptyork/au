import logging
from os.path import commonprefix as get_common_prefix
from pathlib import Path
from pprint import pformat

import click

from au.classroom import Roster
from au.click import RosterOptions, DebugOptions, BasePath


logger = logging.getLogger(__name__)


@click.command()
@click.argument("root_dir", type=BasePath(), default=".")
@RosterOptions(prompt=True, required=True).options
@click.option(
    "--preserve-prefix",
    is_flag=True,
    help="set to preserve the prefix (slug) string common to all repositories",
)
@click.option(
    "-p",
    "--preview",
    is_flag=True,
    help="set to show changes without actually making them",
)
@DebugOptions().options
def rename_roster(
    root_dir: Path,
    roster: Roster,
    preserve_prefix: bool = False,
    preview: bool = False,
    **kwargs,
) -> None:
    """Rename subdirectories to contain students' real names.

    This is generally only useful if student repositories have already been
    cloned using other means. This command uses the same naming logic as does
    `au classroom clone-all`.

    This will rename the subdirectories in ROOT_DIR to contain a students real
    name by matching a the Github ID from the classroom roster to a folder name.
    Any potentially unsafe characters, as well as commas and spaces, are
    replaced with an underscore (`_`). Any characters after the matching github
    id are preserved in order to prevent possible duplicate directory names.

    The purpose is to help with finding and sorting directories by the real
    names of students.

    The resulting name will be:

        [real name]@[github id][suffix]/

    \For example:

        York_Paul@ptyork/

    Directories of students that are not in the roster are skipped entirely. If
    the student's name is found in the directory name, it is likewise skipped as
    it is assumed that the directory has already been renamed.

    If ROOT_DIR is not provided, then the current working directory will be
    assumed.
    """
    logging.basicConfig()

    logger.debug(pformat(root_dir))
    logger.debug(pformat(roster))

    login_dir_map = roster.get_login_dir_map(root_dir)
    common_prefix = get_common_prefix(list(login_dir_map.values()))
    prefix = ""
    if preserve_prefix:
        prefix = common_prefix
    login_dirname_map = roster.get_dir_names(prefix)

    logger.debug(f"Renaming subdirectories in {root_dir}")
    for login, old_dir_name in login_dir_map.items():
        new_dir_name = login_dirname_map.get(login)
        if old_dir_name and new_dir_name and old_dir_name != new_dir_name:
            old_dir = root_dir / old_dir_name
            if preview:
                logger.info(f"Would rename {old_dir_name} to {new_dir_name}")
            else:
                logger.info(f"Renaming {old_dir_name} to {new_dir_name}")
                try:
                    old_dir.rename(new_dir_name)
                except Exception as ex:
                    logger.error(f'Unable to rename "{old_dir}": {ex}')
        else:
            logger.info(f"SKIPPING: {old_dir_name}")


if __name__ == "__main__":
    rename_roster()
