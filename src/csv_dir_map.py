#!/usr/bin/env python3

from typing import Tuple, Dict, List

import csv
import logging
import os

from pathlib import Path

from pprint import pformat

import logging

logger = logging.getLogger(__name__)

def get_dir_map(
    root_dir: str,
    csv_file: str,
    pattern_col: int,
    label_col: int,
    no_header: bool = False,
    ignore_case: bool = False) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    '''
    Read a set of patterns and labels from a CSV file. Use the pattern to find
    matching directories in a specified root folder.
     
    Returns 2 dictionaries:
     * map pattern to label
     * map directory to label
    
    Also returns a list of unmatched patterns.
    '''

    ###############################################################################
    # SETUP AND VALIDATE ARGUMENTS
    ###############################################################################

    _root_dir = Path(os.path.abspath(root_dir))

    if not os.path.isdir(_root_dir):
        raise FileNotFoundError(f"{_root_dir} is not a valid directory")

    _csv_file = Path(os.path.abspath(csv_file))

    if not os.path.isfile(_csv_file):
        raise FileNotFoundError(f"{_csv_file} could not be found")

    ###############################################################################
    # FIND ALL SUBDIRECTORIES
    ###############################################################################

    subdirs = []

    logger.debug(f"Checking {_root_dir} for subdirs")
    for name in os.listdir(_root_dir):
        entry = _root_dir / name
        if entry.is_dir():
            subdirs.append(name)
            logger.debug(f"IS DIR:  {name}")
        else:
            logger.debug(f"NOT DIR: {name}")
    logger.debug(f"found {len(subdirs)} subdirs")

    ###############################################################################
    # PROCESS CSV FILE
    ###############################################################################

    pattern_label_map = {}

    try:
        with open(_csv_file) as _csv_file:
            rdr = csv.reader(_csv_file)

            header_skipped = no_header

            for row in rdr:
                if header_skipped:
                    pattern = row[pattern_col]
                    label = row[label_col]
                    if len(pattern) > 2:
                        pattern_label_map[pattern] = label
                    else:
                        logger.info(f"Skipping Entry: {pattern} -> {label} (pattern too short)")
                else:
                    header_skipped = True

        logger.debug(f"Patterns+Labels Dict:\np{pformat(pattern_label_map)}")

    except Exception as ex:
        logging.error(f"Error reading {_csv_file}: {ex}")
        exit(1)

    ###############################################################################
    # PROCESS ALL SUBDIRECTORIES
    ###############################################################################

    # Sort the list of patterns largest to smallest to avoid potential issues
    # with patterns being substrings of one another

    sorted_patterns = list(pattern_label_map.keys())
    sorted_patterns.sort(key=lambda s: len(s), reverse=True)
    logger.debug(f"Ordered substitution patterns:\n{pformat(sorted_patterns)}")

    # track found patterns so we know which ones we didn't find
    unmatched_patterns = list(pattern_label_map.keys())

    dir_label_map = {}

    for dir in subdirs:

        dir_name = str(dir)
        match_dir = dir_name.lower() if ignore_case else dir_name

        for pattern in sorted_patterns:
            match_pattern = pattern.lower() if ignore_case else pattern
            if match_pattern in match_dir:
                label = pattern_label_map[pattern]
                dir_label_map[dir_name] = label
                if pattern in unmatched_patterns:
                    unmatched_patterns.remove(pattern)
                break

    return pattern_label_map, dir_label_map, unmatched_patterns
