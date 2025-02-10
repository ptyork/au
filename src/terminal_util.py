from typing import Iterable
from os import get_terminal_size
from math import ceil
import re

_MAX_REASONABLE_WIDTH = 120

###############################################################################
# get_max_width
###############################################################################

def get_term_width(max_term_width: int = _MAX_REASONABLE_WIDTH):
    return min(max_term_width, get_terminal_size().columns)


###############################################################################
# draw_line / draw_single_line / draw_double_line
###############################################################################

def draw_single_line(text: str = '', width: int = _MAX_REASONABLE_WIDTH):
    draw_line("━", text, width)

def draw_double_line(text: str = '', width: int = _MAX_REASONABLE_WIDTH):
    draw_line('═', text, width)

def draw_line(char: str = '-', text: str = '', width: int = _MAX_REASONABLE_WIDTH):
    term_width = get_term_width(width)
    if text:
        text = text.strip()
        text_len = len(text) + 2
        if text_len >= width:
            print(char, text)
        else:
            line_len = width - text_len
            left_len = line_len // 2
            right_len = left_len + (line_len % 2)
            print(char * left_len, text, char * right_len)
    else:
        print(char * term_width)


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
        draw_double_line(width=term_width)
        print(title)

    draw_single_line(width=term_width)

    for i in range(row_count):
        for j in range(col_count):
            idx = i + j * row_count
            if idx < len(choices):
                choice_num = idx + 1
                print(f"{choice_num:>2}. {choices[idx]}".ljust(col_len), end = '')
        print()

    draw_single_line(width=term_width)

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

