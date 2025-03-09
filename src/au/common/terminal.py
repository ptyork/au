from typing import Iterable
from os import get_terminal_size, sep
from math import ceil
import re
from pathlib import Path
from beaupy import select


from .drawing import get_line, BoxChars

###############################################################################
# get_term_width
###############################################################################

MAX_REASONABLE_WIDTH = 120


def get_term_width(max_term_width: int = MAX_REASONABLE_WIDTH):
    try:
        term_width = get_terminal_size().columns
    except:
        return max_term_width
    if max_term_width == 0:
        max_term_width = 9999
    return min(max_term_width, term_width)


###############################################################################
# get_line / draw_line / draw_single_line / draw_double_line
###############################################################################


def draw_single_line(text: str = "", max_width: int = MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.HEAVY_HORIZONTAL, text, max_width)


def draw_double_line(text: str = "", max_width: int = MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.DOUBLE_HORIZONTAL, text, max_width)


def draw_line(
    char: str = BoxChars.HEAVY_HORIZONTAL,
    text: str = "",
    max_width: int = MAX_REASONABLE_WIDTH,
) -> None:
    term_width = get_term_width(max_width)
    print(get_line(char, text, term_width))


###############################################################################
# get_choice
###############################################################################


def get_choice(
    choices: Iterable,
    title: str = None,
    prompt: str = "Choose",
    ideal_max_rows: int = 8,
    max_term_width: int = MAX_REASONABLE_WIDTH,
) -> int:
    """
    Allow a user to choose from a list of choices. Display the choices in
    columns if the number of choices exceeds ideal_max_rows.
    """
    term_width = get_term_width(max_term_width)
    ideal_col_count = ceil(len(choices) / ideal_max_rows)
    max_len = max([len(choice) for choice in choices])
    col_len = max_len + 6
    max_col_count = term_width // col_len
    col_count = min(ideal_col_count, max_col_count)
    row_count = ceil(len(choices) / col_count)

    if title:
        draw_double_line(max_width=term_width)
        print(title)
        draw_single_line(max_width=term_width)

    for i in range(row_count):
        for j in range(col_count):
            idx = i + j * row_count
            if idx < len(choices):
                choice_num = idx + 1
                print(f"{choice_num:>2}. {choices[idx]}".ljust(col_len), end="")
        print()
    draw_single_line(max_width=term_width)

    while True:
        try:
            choice = int(input(f"{prompt} >> "))
            assert 0 < choice <= len(choices)
            return choice - 1
        except (AssertionError, ValueError):
            print("!! INVALID CHOICE !!")


###############################################################################
# select_choice
###############################################################################


def select_choice(
    choices: Iterable,
    title: str = None,
    max_rows: int = 8,
    max_term_width: int = MAX_REASONABLE_WIDTH,
) -> int | None:
    term_width = get_term_width(max_term_width)

    if title:
        draw_double_line(max_width=term_width)
        print(title)
        draw_single_line(max_width=term_width)
    return select(
        options=choices, pagination=True, page_size=max_rows, return_index=True
    )


###############################################################################
# select_file
###############################################################################


def select_file(
    root: Path = None,
    filter: str | Iterable[str] = "*",
    title: str = None,
    files_at_top: bool = True,
    max_rows: int = 8,
    max_term_width: int = MAX_REASONABLE_WIDTH,
) -> Path | None:
    """Interactive file picker."""
    if not root:
        root = Path.cwd().resolve()
    term_width = get_term_width(max_term_width)

    if title:
        draw_double_line(max_width=term_width)
        print(title)
        draw_single_line(max_width=term_width)

    path = root
    while True:
        options = []
        options.append(f".{sep}\t\t({path})")
        sel_start = 1
        if path.parent and path.parent != path:
            options.append(f"..{sep}\t\t({path.parent})")
            sel_start = 2
        if isinstance(filter, str):
            files = [file.name for file in path.glob(filter) if file.is_file()]
        else:
            files = []
            for pattern in filter:
                files += [file.name for file in path.glob(pattern) if file.is_file()]
        dirs = [file.name + sep for file in path.iterdir() if file.is_dir()]
        files.sort(key=str.casefold)
        dirs.sort(key=str.casefold)
        all = files + dirs
        if not all:
            sel_start -= 1
        if not files_at_top:
            all.sort(key=str.casefold)
        options.extend(all)

        if not max_rows or max_rows < 3:
            pagination = False
            max_rows = 1  # beaupy blows up if < 1
        else:
            pagination = True

        sel = select(
            options=options,
            cursor_index=sel_start,
            pagination=pagination,
            page_size=max_rows,
        )

        if not sel:
            path = None
            break
        sel = sel.split(sep)[0]
        path = (path / sel).resolve()
        if path.is_file():
            break
    return path


###############################################################################
# select_dir
###############################################################################


def select_dir(
    root: Path = None,
    title: str = None,
    exclude_hidden: bool = True,
    exclude_dunder: bool = True,
    max_rows: int = 8,
    max_term_width: int = MAX_REASONABLE_WIDTH,
) -> Path | None:
    """Interactive directory picker."""
    if not root:
        root = Path.cwd().resolve()
    term_width = get_term_width(max_term_width)

    if title:
        draw_double_line(max_width=term_width)
        print(title)
        draw_single_line(max_width=term_width)

    path = root
    while True:
        options = []
        options.append(f"CHOOSE {path}")
        if path.parent and path.parent != path:
            options.append(f"..{sep}")
        dirs = []
        for file in path.iterdir():
            if not file.is_dir():
                continue
            if exclude_hidden and file.name.startswith("."):
                continue
            if exclude_dunder and file.name.startswith("__"):
                continue
            dirs.append(file.name + sep)
        dirs.sort(key=str.casefold)
        options.extend(dirs)

        if not max_rows or max_rows < 3:
            pagination = False
            max_rows = 1  # beaupy blows up if < 1
        else:
            pagination = True

        sel = select(
            options=options,
            pagination=pagination,
            page_size=max_rows,
            return_index=True,
        )

        if sel == None:
            path = None
            break
        if sel == 0:
            return path
        path = (path / options[sel]).resolve()
    return path


###############################################################################
# clean_ansi
###############################################################################

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str):
    return ANSI_ESCAPE_PATTERN.sub("", text)
