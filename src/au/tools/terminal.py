from typing import Iterable
from os import get_terminal_size
from math import ceil
import re

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

def draw_single_line(text: str = '', max_width: int = MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.HEAVY_HORIZONTAL, text, max_width)

def draw_double_line(text: str = '', max_width: int = MAX_REASONABLE_WIDTH) -> None:
    draw_line(BoxChars.DOUBLE_HORIZONTAL, text, max_width)

def draw_line(char: str = BoxChars.HEAVY_HORIZONTAL,
              text: str = '',
              max_width: int = MAX_REASONABLE_WIDTH) -> None:
    term_width = get_term_width(max_width)
    print(get_line(char, text, term_width))

###############################################################################
# get_choice
###############################################################################

def get_choice(choices: Iterable,
               title: str = None,
               prompt: str = "Choose",
               ideal_max_rows: int = 8,
               max_term_width: int = MAX_REASONABLE_WIDTH) -> int:
    
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
def strip_ansi(text: str):
    return ansi_escape.sub('', text)

if __name__ == "__main__":
    ...