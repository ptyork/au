from enum import Enum, auto
from typing import Dict, overload

from pathlib import Path
from pprint import pformat

import logging

logger = logging.getLogger(__name__)


class FileType(Enum):
    """
    Enum for FILE, DIRECTORY or BOTH
    """

    FILE = auto()
    DIRECTORY = auto()
    BOTH = auto()


@overload
def label_dir(
    pattern_dict: Dict[str, str],
    search_dir: Path,
    file_type: FileType = FileType.FILE,
    ignore_case: bool = True,
    skip_hidden: bool = True,
) -> Dict[str, str]: ...


@overload
def label_dir(
    pattern_dict: Dict[str, str],
    search_dir: str,
    file_type: FileType = FileType.FILE,
    ignore_case: bool = True,
    skip_hidden: bool = True,
) -> Dict[str, str]: ...


def label_dir(
    pattern_dict: Dict[str, str],
    search_dir: Path | str,
    file_type: FileType = FileType.FILE,
    ignore_case: bool = True,
    skip_hidden: bool = True,
) -> Dict[str, str]:
    """
    Given a `pattern_dict` containing search patterns as keys and labels as
    values, return a dictionary of all files or subdirectories (sub-objects) of
    `search_dir` with an associated label. A label `pattern_dict` is applied to
    a sub-object if the its name contains the corresponding pattern. If no
    pattern is not found in the dir, then the associated label is set to None.

    For example, assume pattern_dict of:
        {
            'foo': 'fat', 'bar': 'bat'
        }

    Also assume root_dir contains 3 entries:
        giga_foo    kilo_bar    mega_moo

    This function will return:

        {
            'giga_foo': 'fat', 'baby_bar': 'bat', 'mega_moo': None
        }
    """

    if isinstance(search_dir, str):
        root_dir = Path(search_dir).resolve()
    elif isinstance(search_dir, Path):
        root_dir = search_dir.resolve()
    else:
        raise ValueError("root_dir must be a str or a Path")

    if not root_dir.is_dir():
        raise FileNotFoundError(f"{root_dir} is not a valid directory")

    obj_label_map = {}

    logger.debug(f"Checking {root_dir} for subdirs")
    for obj in root_dir.iterdir():
        if obj.is_dir() and file_type == FileType.FILE:
            continue
        if obj.is_file() and file_type == FileType.DIRECTORY:
            continue
        if skip_hidden and obj.name.startswith("."):
            continue
        obj_label_map[obj.name] = None

    logger.debug(f"found {len(obj_label_map)} subdirs")

    # Sort the list of patterns largest to smallest to avoid potential issues
    # with patterns being substrings of one another

    sorted_patterns = list(pattern_dict.keys())
    sorted_patterns.sort(key=lambda s: len(s), reverse=True)
    logger.debug(f"Ordered substitution patterns:\n{pformat(sorted_patterns)}")

    for obj_name in obj_label_map:
        match_obj_name = obj_name.lower() if ignore_case else obj_name
        for pattern in sorted_patterns:
            match_pattern = pattern.lower() if ignore_case else pattern
            if match_pattern in match_obj_name:
                label = pattern_dict[pattern]
                obj_label_map[obj_name] = label
                break

    return obj_label_map
