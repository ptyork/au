from collections.abc import Iterable
from os import get_terminal_size, sep
from math import ceil
import re
from pathlib import Path

from getrich import FileChooser, FilterChooser, ChooserStyles

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
# select_choice / select_value
###############################################################################

def _select(
    choices: Iterable,
    title: str = '',
    borders: bool = True,
    max_rows: int = 10,
    filtered: bool = False,
) -> tuple[str, int] | tuple[None, None]:
    styles: ChooserStyles = {
        "show_border": borders,
        "selection_style": "bold bright_white on grey30",
    }
    return FilterChooser(
        choices=choices,
        title_text=title,
        height=max_rows,
        styles=styles,
        disable_filtering=not filtered,
    ).run()

def select_choice(
    choices: Iterable,
    title: str = '',
    borders: bool = True,
    max_rows: int = 10,
    filtered: bool = False,
) -> int | None:
    _, idx = _select(
        choices=choices,
        title=title,
        borders=borders,
        max_rows=max_rows,
        filtered=filtered,
    )
    return idx

def select_value(
    choices: Iterable,
    title: str = '',
    borders: bool = True,
    max_rows: int = 10,
    filtered: bool = False,
) -> str | None:
    val, _ = _select(
        choices=choices,
        title=title,
        borders=borders,
        max_rows=max_rows,
        filtered=filtered,
    )
    return val


###############################################################################
# select_file
###############################################################################


def select_file(
    initial_path: Path = Path("."),
    title: str  = "",
    glob: str | Iterable[str] = "*",
    exclude_hidden: bool = True,
    exclude_dunder: bool = True,
    files_at_top: bool = True,
    max_rows: int = 10,
    borders: bool = True,
) -> Path | None:
    """Interactive file picker."""
    styles: ChooserStyles = {
        "show_border": False,
        "selection_style": "bold bright_white on grey30",
    }
    return FileChooser(
        initial_path=initial_path,
        files_at_top=files_at_top,
        exclude_hidden=exclude_hidden,
        exclude_dunder=exclude_dunder,
        glob=glob,
        title_text=title,
        height=max_rows,
        styles=styles,
    ).run()


###############################################################################
# select_dir
###############################################################################


def select_dir(
    initial_path: Path = Path("."),
    title: str = "",
    exclude_hidden: bool = True,
    exclude_dunder: bool = True,
    max_rows: int = 10,
    borders: bool = True,
) -> Path | None:
    """Interactive directory picker."""
    styles: ChooserStyles = {
        "show_border": borders,
        "selection_style": "bold bright_white on grey30",
    }
    return FileChooser(
        initial_path=initial_path,
        choose_dirs=True,
        exclude_hidden=exclude_hidden,
        exclude_dunder=exclude_dunder,
        title_text=title,
        height=max_rows,
        styles=styles,
    ).run()

    if initial_path:
        initial_path = initial_path.resolve()
    else:
        initial_path = Path.cwd().resolve()

    path = initial_path
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
            title=title,
            instructions='\n\n[gray70 italic]↑ or ↓ to choose | enter to select | esc to cancel[/gray70 italic]',
            borders=borders,
            cursor_style="bold bright_white",
            selected_style="bold bright_white on grey30",
            selected_fill=True,
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
