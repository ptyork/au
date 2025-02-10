#!/usr/bin/env python3
 
import argparse
import logging
import os
import re
from pathlib import Path
from pprint import pformat

from csv_dir_map import get_dir_map

_base_logging_level = logging.INFO

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(_base_logging_level)

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

parser.description = '''
Rename the subdirectories in a specified directory to contain a students real
name by matching a the Github ID from the classroom roster to a folder name. Any
potentially unsafe characters, as well as commas and spaces, are replaced with
an underscore (`_`). Any characters after the matching github id are preserved
in order to prevent possible duplicate directory names.

The purpose is to help with finding and sorting directories by the real names of
students.

The resulting name will be:

    [prefix][real name]-[github id][suffix]

For example:

    assn-1-York_Paul-ptyork

Windows Example Usage:
  py gh_rename_roster.py .\\classroom_roster.csv .\\subfolder\\
  
Linux / MacOS Example Usage:
  python3 gh_rename_roster.py ./classroom_roster.csv ./subfolder/
'''

parser.add_argument("csv_file", type=str, help="the CSV file with the name, pattern ")
parser.add_argument("root_dir", type=str, help="the directory containing the subdirectories to rename")
parser.add_argument("-d", "--debug", help="set to enable detailed output", action="store_true")
parser.add_argument("-q", "--quiet", help="set to reduce output to errors only", action="store_true")
parser.add_argument("-p", "--preview", help="set to show changes without actually making them", action="store_true")

args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)
elif args.quiet:
    logger.setLevel(logging.WARNING)

###############################################################################
# SETUP AND VALIDATE ARGUMENTS
###############################################################################

root_dir = Path(os.path.abspath(args.root_dir))

if not os.path.isdir(root_dir):
    logger.error(f"{root_dir} is not a valid directory")
    exit(1)

csv_file = Path(os.path.abspath(args.csv_file))

if not os.path.isfile(csv_file):
    logger.error(f"{csv_file} could not be found")
    exit(1)

try:
    id_student_map, dir_student_map, _ = get_dir_map(root_dir, args.csv_file, 1, 0)
    student_id_map = dict((v,k) for k,v in id_student_map.items())

    logger.debug(pformat(dir_student_map))
except Exception as ex:
    logger.error(f"Error encountered while processing {args.csv_file}: {ex}")
    exit(1)


###############################################################################
# RENAME SUBDIRECTORIES
###############################################################################

re_invalid = re.compile(r'([<>:"/\\\,|?*]|\s)+')

logger.debug(f"Renaming subdirectories in {root_dir}")
for dir_name in os.listdir(root_dir):
    subdir = root_dir / dir_name
    if dir_name in dir_student_map and subdir.is_dir():
        student_name = dir_student_map[dir_name]
        student_id = student_id_map[student_name]
        safe_student_name = re_invalid.sub('_', student_name)
        full_name = safe_student_name + '-' + student_id
        new_dir_name = dir_name.replace(student_id, full_name)

        if args.preview:
            logger.info(f"Would rename {dir_name} to {new_dir_name}")
        else:
            logger.info(f"Renaming {dir_name} to {new_dir_name}")
            try:
                logger.debug(f"os.rename({dir_name}, {new_dir_name})")
                os.rename(dir_name, new_dir_name)
            except Exception as ex:
                logger.error(f'Unable to rename "{dir_name}": {ex}')
    else:
        logger.debug(f"skipping: {dir_name}")
