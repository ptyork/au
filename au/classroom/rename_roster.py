#!/usr/bin/env python3

import click 

from os.path import commonprefix as get_common_prefix
from io import TextIOWrapper
import re
from pathlib import Path
from pprint import pformat

from au.lib.common.csv_util import dict_from_csv
from au.lib.common.dir_utils import get_dir_map

import logging
_base_logging_level = logging.INFO
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(_base_logging_level)

@click.command()
@click.argument("root_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.argument("roster", type=click.File())
@click.option("-r", "--remove-prefix", is_flag=True, help="set to remove any prefix string common to all subdirs")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
@click.option("-p", "--preview", is_flag=True, help="set to show changes without actually making them")
def rename_roster(root_dir: Path,
                  roster: TextIOWrapper|Path,
                  remove_prefix: bool = False,
                  preview: bool = False,
                  debug: bool = False,
                  quiet: bool = False) -> None:
    '''
    Rename subdirectories to contain students' real names
    
    \b
    Required Arguments:
      ROOT-DIR
        the base directory containing the files subdirectories to be renamed
      ROSTER
        the GitHub Classroom roster file (usually named `classroom_roster.csv`)
    
    Rename the subdirectories in ROOT-DIR to contain a students real name by
    matching a the Github ID from the classroom roster to a folder name. Any
    potentially unsafe characters, as well as commas and spaces, are replaced
    with an underscore (`_`). Any characters after the matching github id are
    preserved in order to prevent possible duplicate directory names.

    The purpose is to help with finding and sorting directories by the real
    names of students.

    \b
    The resulting name will be:
        [prefix][real name]@[github id][suffix]/

    \b
    For example:
        assn-1-York_Paul@ptyork/

    \b
    And if the --remove-prefix flag is set, the prefix will be removed:
        York_Paul@ptyork/

    Directories of students that are not in the roster are skipped entirely. If
    the student's name is found in the directory name, it is likewise skipped as
    it is assumed that the directory has already been renamed.

    \b 
    Windows Example Usage:
        au classroom rename_roster .\\subfolder\\ .\\classroom_roster.csv
    
    \b
    Linux / MacOS Example Usage:
        python3 gh_rename_roster.py ./subfolder/ ./classroom_roster.csv
    '''

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)

    logger.debug(pformat(root_dir))
    logger.debug(pformat(roster))

    try:
        id_student_map = dict_from_csv(roster, 'github_username', 'identifier')
        logger.debug(pformat(id_student_map))
        dir_student_map = get_dir_map(id_student_map, root_dir)
        logger.debug(pformat(id_student_map))
        student_id_map = dict((v,k) for k,v in id_student_map.items())
        logger.debug(pformat(dir_student_map))

    except Exception as ex:
        logger.error(f"Error encountered while processing roster: {ex}")
        exit(1)

    common_prefix = get_common_prefix(list(dir_student_map.keys()))
    logger.debug(f"Common Prefix: {common_prefix}")

    re_invalid = re.compile(r'([<>:"/\\\,|?*]|\s)+')

    logger.debug(f"Renaming subdirectories in {root_dir}")
    for sub_dir in root_dir.iterdir():
        if dir_student_map.get(sub_dir.name) and sub_dir.is_dir():
            student_name = dir_student_map[sub_dir.name]
            student_id = student_id_map[student_name]
            safe_student_name = re_invalid.sub('_', student_name)
            safe_student_name = safe_student_name.replace('__', '_')
            if safe_student_name in sub_dir.name:
                logger.debug(f"ALREADY RENAMED: {sub_dir}")
                continue
            full_name = safe_student_name + '@' + student_id
            new_dir_name = sub_dir.name.replace(student_id, full_name)
            if remove_prefix:
                new_dir_name = new_dir_name.removeprefix(common_prefix)
            new_dir = root_dir / new_dir_name

            if preview:
                logger.info(f"Would rename {sub_dir} to {new_dir}")
            else:
                logger.info(f"Renaming {sub_dir} to {new_dir}")
                try:
                    sub_dir.rename(new_dir)
                except Exception as ex:
                    logger.error(f'Unable to rename "{sub_dir}": {ex}')
        else:
            logger.debug(f"SKIPPING: {sub_dir}")

if __name__ == '__main__':
    rename_roster()
