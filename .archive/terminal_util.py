from typing import Iterable, List
from enum import Enum
from os import get_terminal_size
from math import ceil
import re

class BoxChars(Enum):
    LIGHT_HORIZONTAL = '\u2500'
    HEAVY_HORIZONTAL = '\u2501'
    LIGHT_VERTICAL = '\u2502'
    HEAVY_VERTICAL = '\u2503'
    LIGHT_DOWN_AND_RIGHT = '\u250c'
    HEAVY_DOWN_AND_RIGHT = '\u250f'
    LIGHT_DOWN_AND_LEFT = '\u2510'
    HEAVY_DOWN_AND_LEFT = '\u2513'
    LIGHT_UP_AND_RIGHT = '\u2514'
    HEAVY_UP_AND_RIGHT = '\u2517'
    LIGHT_UP_AND_LEFT = '\u2518'
    HEAVY_UP_AND_LEFT = '\u251b'
    LIGHT_VERTICAL_AND_RIGHT = '\u251c'
    HEAVY_VERTICAL_AND_RIGHT = '\u2523'
    LIGHT_VERTICAL_AND_LEFT = '\u2524'
    HEAVY_VERTICAL_AND_LEFT = '\u252b'
    LIGHT_DOWN_AND_HORIZONTAL = '\u252c'
    HEAVY_DOWN_AND_HORIZONTAL = '\u2533'
    LIGHT_UP_AND_HORIZONTAL = '\u2534'
    HEAVY_UP_AND_HORIZONTAL = '\u253b'
    LIGHT_VERTICAL_AND_HORIZONTAL = '\u253c'
    HEAVY_VERTICAL_AND_HORIZONTAL = '\u254b'
    LIGHT_DOUBLE_DASH_HORIZONTAL = '\u254c'
    HEAVY_DOUBLE_DASH_HORIZONTAL = '\u254d'
    LIGHT_DOUBLE_DASH_VERTICAL = '\u254e'
    HEAVY_DOUBLE_DASH_VERTICAL = '\u254f'
    DOUBLE_HORIZONTAL = '\u2550'
    DOUBLE_VERTICAL = '\u2551'
    DOUBLE_DOWN_AND_RIGHT = '\u2554'
    DOUBLE_DOWN_AND_LEFT = '\u2557'
    DOUBLE_UP_AND_RIGHT = '\u255a'
    DOUBLE_UP_AND_LEFT = '\u255d'
    DOUBLE_VERTICAL_AND_RIGHT = '\u2560'
    DOUBLE_VERTICAL_AND_LEFT = '\u2563'
    DOUBLE_DOWN_AND_HORIZONTAL = '\u2566'
    DOUBLE_UP_AND_HORIZONTAL = '\u2569'
    DOUBLE_VERTICAL_AND_HORIZONTAL = '\u256c'
    DOUBLE_VERTICAL_AND_HEAVY_RIGHT = '\u2561'
    DOUBLE_VERTICAL_AND_HEAVY_LEFT = '\u2562'
    DOUBLE_DOWN_AND_HEAVY_HORIZONTAL = '\u2564'
    DOUBLE_UP_AND_HEAVY_HORIZONTAL = '\u2567'
    DOUBLE_VERTICAL_AND_HEAVY_HORIZONTAL = '\u256a'
    LIGHT_VERTICAL_AND_DOUBLE_RIGHT = '\u255f'
    LIGHT_VERTICAL_AND_DOUBLE_LEFT = '\u2562'
    LIGHT_DOWN_AND_DOUBLE_HORIZONTAL = '\u2565'
    LIGHT_UP_AND_DOUBLE_HORIZONTAL = '\u2568'
    LIGHT_VERTICAL_AND_DOUBLE_HORIZONTAL = '\u256b'
    LIGHT_ARC_DOWN_AND_RIGHT = '\u256d'
    LIGHT_ARC_DOWN_AND_LEFT = '\u256e'
    LIGHT_ARC_UP_AND_LEFT = '\u256f'
    LIGHT_ARC_UP_AND_RIGHT = '\u2570'
    HEAVY_ARC_DOWN_AND_RIGHT = '\u2571'
    HEAVY_ARC_DOWN_AND_LEFT = '\u2572'
    HEAVY_ARC_UP_AND_LEFT = '\u2573'
    HEAVY_ARC_UP_AND_RIGHT = '\u2574'

    def __str__(self):
        return self.value


_MAX_REASONABLE_WIDTH = 120

###############################################################################
# get_max_width
###############################################################################

def get_term_width(max_term_width: int = _MAX_REASONABLE_WIDTH):
    return min(max_term_width, get_terminal_size().columns)


###############################################################################
# get_line / draw_line / draw_single_line / draw_double_line
###############################################################################

def draw_single_line(text: str = '', max_width: int = _MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.HEAVY_HORIZONTAL, text, max_width)

def draw_double_line(text: str = '', max_width: int = _MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.HEAVY_DOUBLE_DASH_HORIZONTAL, text, max_width)

def draw_line(char: str = BoxChars.HEAVY_HORIZONTAL,
              text: str = '',
              max_width: int = _MAX_REASONABLE_WIDTH) -> None:
    term_width = get_term_width(max_width)
    print(get_line(char, text, term_width))

def get_line(char: str = BoxChars.HEAVY_HORIZONTAL,
             text: str = '',
             width: int = _MAX_REASONABLE_WIDTH) -> str:
    char = str(char)
    if text:
        text = text.strip()
        text_len = len(text) + 2
        if text_len >= width:
            return f"{char} {text}"
        else:
            line_len = width - text_len
            left_len = line_len // 2
            right_len = left_len + (line_len % 2)
            return f"{char * left_len} {text} {char * right_len}"
    else:
        return char * width


###############################################################################
# get_table_header / get_table_row / get_md_table_header / get_md_table_row
###############################################################################

def _get_filled_width(col_widths: List[int], width: int) -> List[int]:
    filled_widths = col_widths.copy()
    fill_cols = [i for i in range(len(col_widths)) if col_widths[i] == 0]
    if not fill_cols:
        return filled_widths
    total_widths = sum(col_widths)
    remaining_width = width - total_widths - len(filled_widths) + 1
    fill_width = remaining_width // len(fill_cols)
    for col in fill_cols:
        filled_widths[col] = fill_width
    return filled_widths

def _align_value(value: str, width: int, align: int, truncate: bool = False) -> str:
    if len(value) > width and truncate:
        value = value[:width-1] + '…'
    if align == 0:  # center
        value = value.center(width)
    elif align > 0: # right
        value = value.rjust(width - 1)
        if len(value) < width:
            value = value + ' '
    else:           # left
        value = value.ljust(width - 1)
        if len(value) < width:
            value = ' ' + value
    return value
    
def get_table_header(
        header_cols: List[str],
        col_widths: List[int],
        col_alignments: List[int] = None,
        max_width: int = _MAX_REASONABLE_WIDTH) -> str:
    width = get_term_width(max_width)
    col_widths = _get_filled_width(col_widths, width)
    header_lines = [
        str(BoxChars.HEAVY_HORIZONTAL) * width for width in col_widths
    ]
    if not col_alignments:
        col_alignments = [0 for _ in col_widths]
    lines = []
    lines.append(str(BoxChars.HEAVY_DOWN_AND_HORIZONTAL).join(header_lines))
    lines.append(get_table_row(header_cols, col_widths, col_alignments, max_width=width))
    lines.append(str(BoxChars.HEAVY_VERTICAL_AND_HORIZONTAL).join(header_lines))
    return '\n'.join(lines)

def get_table_row(
        values: List[str],
        col_widths: List[int],
        col_alignments: List[int] = None,
        col_truncations: List[bool] = None,
        max_width: int = _MAX_REASONABLE_WIDTH) -> str:
    width = get_term_width(max_width)
    col_widths = _get_filled_width(col_widths, width)
    formatted_values = []
    for i in range(len(values)):
        text = str(values[i])
        col_width = col_widths[i]
        # default to left aligned
        align = -1 if not col_alignments else col_alignments[i]
        # default to truncate value
        truncate = True if not col_truncations else col_truncations[i]
        text = _align_value(text, col_width, align, truncate)
        formatted_values.append(text)
    delim = str(BoxChars.HEAVY_VERTICAL)
    return delim.join(formatted_values)

def get_md_table_header(
        header_cols: List[str],
        col_widths: List[int],
        col_alignments: List[int] = None,
        width: int = 100) -> str:
    actual_width = width - 2
    col_widths = _get_filled_width(col_widths, actual_width)
    header_lines = []
    for i in range(len(col_widths)):
        col_width = col_widths[i]
        # default to left aligned
        align = -1 if not col_alignments else col_alignments[i]
        if align == 0:
            header_lines.append(':' + '-' * (col_width-2) + ':')
        elif align > 0:
            header_lines.append('-' * (col_width-1) + ':')
        else:
            header_lines.append('-' * col_width)
    lines = []
    lines.append(get_md_table_row(header_cols, col_widths, col_alignments, width=width))
    lines.append('|' + '|'.join(header_lines))
    return '\n'.join(lines)

def get_md_table_row(
        values: List[str],
        col_widths: List[int],
        col_alignments: List[int] = None,
        col_truncations: List[bool] = None,
        width: int = 100) -> str:
    actual_width = width - 1  # account for left-most `|``
    col_widths = _get_filled_width(col_widths, actual_width)
    formatted_values = []
    for i in range(len(values)):
        text = str(values[i])
        col_width = col_widths[i]
        # default to left aligned
        align = -1 if not col_alignments else col_alignments[i]
        # default to not truncate value
        truncate = False if not col_truncations else col_truncations[i]
        text = _align_value(text, col_width, align, truncate)
        formatted_values.append(text)
    return '|' + '|'.join(formatted_values)



###############################################################################
# get_course
###############################################################################

def get_choice(choices: Iterable,
               title: str = None,
               prompt: str = "Choose",
               ideal_max_rows: int = 8,
               max_term_width: int = _MAX_REASONABLE_WIDTH) -> int:
    
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
                print(f"{choice_num:>2}. {choices[idx]}".ljust(col_len), end = '')
        print()

    draw_single_line(max_width=term_width)

    while True:
        try:
            choice = int(input(f'{prompt} >> '))
            assert 0 < choice <= len(choices)
            return choice - 1
        except (AssertionError, ValueError):
            print('!! INVALID CHOICE !!')


###############################################################################
# clean_ansi
###############################################################################

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def clean_ansi(text: str):
    return ansi_escape.sub('', text)

