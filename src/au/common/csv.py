from typing import Dict

import csv as csv_lib
from io import TextIOBase, StringIO
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


def dict_from_csv(
    csv: Path | str | TextIOBase,
    key_col: int | str,
    val_col: int | str,
    no_header: bool = False,
) -> Dict[any, any]:
    """
    Convert a CSV formatted text into a dictionary using the `key_col` column in
    the CSV as key and `val_col` for values. If duplicate key's are found in the
    CSV, the value will be derived from the last one processed. All keys and
    values will be of type str.
    """

    csv_dict = {}
    open_file = None

    try:
        logger.debug(f"Checking {csv}")
        if isinstance(csv, str):
            logger.debug(f"Found str")
            csv_iter = StringIO(csv)
        elif isinstance(csv, Path):
            logger.debug(f"Found Path")
            if not csv.exists():
                raise FileNotFoundError()
            logger.debug(f"Opening {csv}")
            open_file = open(csv)
            csv_iter = open_file
        elif isinstance(csv, TextIOBase):
            logger.debug(f"Found TextIOBase")
            csv_iter = csv
        else:
            raise ValueError("csv is not a string, stream, or Path")

        if isinstance(key_col, int) and isinstance(val_col, int):
            key_idx = key_col
            val_idx = val_col
        elif isinstance(key_col, str) and isinstance(val_col, str):
            if no_header:
                raise ValueError(
                    "no_header cannot be True if key_col and val_col are str"
                )
            key_idx = None
            val_idx = None
        else:
            raise ValueError("key_col and val_col must both either be int or str")

        logger.debug(f"Using key_idx={key_idx} and val_idx={val_idx}")

        rdr = csv_lib.reader(csv_iter)

        logger.debug(f"{rdr}")

        header_skipped = no_header

        for row in rdr:
            logger.debug(f"PROCESSING: {row}")
            if header_skipped:
                key = row[key_idx].strip()
                val = row[val_idx].strip()
                if key:
                    csv_dict[key] = val
            else:
                if not key_idx:
                    # Read header to match column to key_idx and val_idx.
                    # Allows unhandled ValueError to be raised as this is fatal.
                    row_lower = [text.lower() for text in row]
                    key_idx = row_lower.index(key_col.lower())
                    val_idx = row_lower.index(val_col.lower())
                header_skipped = True
    except:
        raise
    finally:
        if open_file:
            open_file.close()
        return csv_dict
