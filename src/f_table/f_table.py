from typing import List
from dataclasses import dataclass
from os import get_terminal_size
import re
from textwrap import wrap

from .BoxChars import BoxChars

###############################################################################
# get_term_width
###############################################################################

MAX_REASONABLE_WIDTH = 120

def get_term_width(max_term_width: int = MAX_REASONABLE_WIDTH):
    try:
        term_width = get_terminal_size().columns
    except:         # pylint:disable=bare-except
        return max_term_width
    if max_term_width == 0:
        max_term_width = 9999
    return min(max_term_width, term_width)

###############################################################################
# TableStyles
###############################################################################

class TableStyle:
    def __init__(self):
        self.top_border = True
        self.bottom_border = True
        self.terminal_style = True
        self.allow_lazy_header = True
        self.force_header = False
        self.align_char = None

        self.cell_padding = 1
        self.min_width = 1

        self.no_header_top_line = BoxChars.LIGHT_HORIZONTAL.value
        self.no_header_top_delimiter = BoxChars.LIGHT_DOWN_AND_HORIZONTAL.value
        self.no_header_top_left = BoxChars.LIGHT_DOWN_AND_RIGHT.value
        self.no_header_top_right = BoxChars.LIGHT_DOWN_AND_LEFT.value

        self.header_top_line = BoxChars.LIGHT_HORIZONTAL.value
        self.header_top_delimiter = BoxChars.LIGHT_DOWN_AND_HORIZONTAL.value
        self.header_top_left = BoxChars.LIGHT_DOWN_AND_RIGHT.value
        self.header_top_right = BoxChars.LIGHT_DOWN_AND_LEFT.value

        self.header_delimiter = BoxChars.LIGHT_VERTICAL.value
        self.header_left = BoxChars.LIGHT_VERTICAL.value
        self.header_right = BoxChars.LIGHT_VERTICAL.value

        self.header_bottom_line = BoxChars.LIGHT_HORIZONTAL.value
        self.header_bottom_delimiter = BoxChars.LIGHT_VERTICAL_AND_HORIZONTAL.value
        self.header_bottom_left = BoxChars.LIGHT_VERTICAL_AND_RIGHT.value
        self.header_bottom_right = BoxChars.LIGHT_VERTICAL_AND_LEFT.value

        self.values_delimiter = BoxChars.LIGHT_VERTICAL.value
        self.values_left = BoxChars.LIGHT_VERTICAL.value
        self.values_right = BoxChars.LIGHT_VERTICAL.value

        self.values_bottom_line = BoxChars.LIGHT_HORIZONTAL.value
        self.values_bottom_delimiter = BoxChars.LIGHT_UP_AND_HORIZONTAL.value
        self.values_bottom_left = BoxChars.LIGHT_UP_AND_RIGHT.value
        self.values_bottom_right = BoxChars.LIGHT_UP_AND_LEFT.value

class BasicScreenStyle(TableStyle): ...

class NoBorderScreenStyle(TableStyle):
    def __init__(self):
        super().__init__()
        self.top_border = False
        self.bottom_border = False
        self.header_left = ''
        self.values_left = ''
        self.header_top_left = ''
        self.header_bottom_left = ''
        self.values_bottom_left = ''
        self.header_right = ''
        self.values_right = ''
        self.header_top_right = ''
        self.header_bottom_right = ''
        self.values_bottom_right = ''

class MarkdownStyle(TableStyle):
    def __init__(self):
        super().__init__()
        self.top_border = False
        self.bottom_border = False
        self.terminal_style = False
        self.allow_lazy_header = False
        self.force_header = True
        self.align_char = ':'

        self.min_width = 3

        self.header_delimiter = '|'
        self.header_left = '|'
        self.header_right = '|'

        self.header_bottom_line = '-'
        self.header_bottom_delimiter = '|'
        self.header_bottom_left = '|'
        self.header_bottom_right = '|'

        self.values_delimiter = '|'
        self.values_left = '|'
        self.values_right = '|'


###############################################################################
# ColDef (for tables)
###############################################################################

_format_spec_pattern = re.compile(
     r'((?P<fill>.)?(?P<align>[<>=^]))?'
     r'(?P<sign>[+\- ])?'
     r'(?P<alternate>[z#])?'
     r'(?P<zero>0)?'
     r'(?P<width>\d+)?'
     r'(?P<grouping_option>[_,])?'
     r'(?P<precision>\.\d+)?'
     r'(?P<type>[bcdeEfFgGnosxX%])?'
     r'(?P<table_config>[ANT]+)?')

@dataclass
class ColDef:
    width: int|None = None
    align: str = '<'
    auto_fill: bool = False
    wrap: bool = True
    truncate: bool = False
    _format_spec: str = ''

    def get_format_string(self) -> str:
        if self._format_spec:
            return f"{{:{self._format_spec}}}"
        else:
            return self.get_fallback_format_string()

    def get_fallback_format_string(self) -> str:
        return f"{{:{self.align}{self.width}}}"

    def format(self, value: any) -> str:
        # "Inner" format
        format_string = f"{{:{self._format_spec}}}"
        text = format_string.format(value)

        # "Outer" format
        return self.format_text(text)


    def format_text(self, text: str) -> str:
        if len(text) > self.width and self.truncate:
            text = text[:self.width-1] + '…'

        if self.align == '^':
            text = text.strip().center(self.width)
        elif self.align == '>':
            text = text.strip().rjust(self.width)
        else:
            text = text.ljust(self.width)

        return text

    @staticmethod
    def parse(text) -> 'ColDef':
        match = _format_spec_pattern.match(text)
        if not match:
            raise ValueError(f"Invalid format specifier for column: {text}")
        spec = match.groupdict()
        align = spec['align']
        if not align or align == "=":
            align = ''
        width = spec['width']
        if not width:
            width = None
        else:
            width = int(width)

        auto_size = False
        wrap_line = True
        truncate = False

        table_config = spec['table_config']
        if table_config:
            if "A" in table_config:
                auto_size = True
            if "N" in table_config:
                wrap_line = False
            if "T" in table_config:
                truncate = True
            format_spec = text.removesuffix(table_config)
        else:
            format_spec = text

        # if format spec is just a number, then just toss it to avoid
        # inadvertent right-aligned numbers.
        try:
            _ = int(format_spec)
            format_spec = ''
        except ValueError:
            pass

        return ColDef(
            width=width,
            align=align,
            auto_fill=auto_size,
            wrap=wrap_line,
            truncate=truncate,
            _format_spec=format_spec
        )

###############################################################################
# get_table_header / get_table_row
###############################################################################

def _parse_col_defs(col_defs: List[str|ColDef]) -> None:
    for i in range(len(col_defs)):
        col_val = col_defs[i]
        if isinstance(col_val, str):
            col_defs[i] = ColDef.parse(col_val)
        elif isinstance(col_val, ColDef):
            pass
        else:
            raise ValueError("Column definitions contain an invalid value")

def _get_col_defs_for_table(values: List[List[any]]) -> List[ColDef]:
    max_cols = max([len(row) for row in values])
    col_defs = [ColDef() for _ in range(max_cols)]
    for col_idx in range(max_cols):
        max_width = max([len(str(row[col_idx])) for row in values])
        col_defs[col_idx].width = max_width
    return col_defs

def _adjust_col_defs(col_defs: List[ColDef],
                     table_data: List[List[any]],
                     table_width: int,
                     style: TableStyle) -> None:
    # ADD MISSING COL DEFS
    max_cols = max([len(row) for row in table_data])
    diff = max_cols - len(col_defs)
    if diff:
        for _ in range(diff):
            col_defs.append(ColDef())

    # ADJUST WIDTHS OF FIELDS TO MATCH REALITY
    for col_idx in range(max_cols):
        max_width = max([len(str(row[col_idx])) for row in table_data])
        col_def = col_defs[col_idx]
        if not col_def.width:
            col_def.width = max_width
        if col_def.width < style.min_width:
            col_def.width = style.min_width

    # ADJUST AUTO-FILL COLS TO FILL REMAINING SPACE AVAILABLE IN TOTAL TABLE_WIDTH
    if not table_width:
        return

    padding_len = style.cell_padding * 2 * len(col_defs)
    border_len = len(style.values_left) + len(style.values_right)
    delims_len = len(style.values_delimiter) * (len(col_defs) - 1)
    non_text_len = padding_len + border_len + delims_len
    total_len = non_text_len + sum([c.width for c in col_defs])

    fill_cols = [col_idx for col_idx in range(len(col_defs)) if col_defs[col_idx].auto_fill]
    if not fill_cols:
        if total_len <= table_width:
            return
        else:
            largest_col = col_defs[0]
            largest_col_idx = 0
            for col_idx in range(1, len(col_defs)):
                col_def = col_defs[col_idx]
                if col_def.width > largest_col.width:
                    largest_col = col_def
                    largest_col_idx = col_idx
            largest_col.auto_fill = True
            fill_cols.append(largest_col_idx)

    fixed_len = sum([c.width for c in col_defs if not c.auto_fill])

    remaining_width = table_width - fixed_len - non_text_len
    fill_width = remaining_width // len(fill_cols)

    if fill_width < style.min_width:
        raise ValueError("Unable to expand columns to fit table width because existing columns are too wide")

    remainder = remaining_width % len(fill_cols)
    for col_idx in fill_cols:
        new_width = fill_width
        if remainder:
            new_width += 1
            remainder -= 1
        col_defs[col_idx].width = new_width


###############################################################################
# get_table_row
###############################################################################

def _get_table_row(values: List[str],
                   style: TableStyle = NoBorderScreenStyle(),
                   col_defs: List[str|ColDef] = None,
                   table_width: int = None,
                   lazy_end: bool = False,
                   is_header: bool = False) -> str:

    if not table_width and style.terminal_style:
        table_width = get_term_width()
    if not col_defs:
        col_defs = _get_col_defs_for_table([values])
    else:
        _parse_col_defs(col_defs)
    _adjust_col_defs(col_defs, [values], table_width, style)

    col_count = len(values)

    formatted_values = []
    for col_idx in range(col_count):
        col_val = values[col_idx]
        col_def = col_defs[col_idx]
        text = col_def.format(col_val)
        formatted_values.append(text)

    all_col_lines = []
    for col_idx in range(col_count):
        col_lines = []
        col_def = col_defs[col_idx]
        text = formatted_values[col_idx]
        split = text.splitlines()
        if not split:
            split = ['']
        for line in split:
            wrapped = wrap(line, width=col_def.width)
            if wrapped:
                for wrapped_line in wrapped:
                    col_lines.append(wrapped_line)
            else:
                col_lines.append(line)
            all_col_lines.append(col_lines)

    max_rows = max([len(col) for col in all_col_lines])

    if max_rows == 1:
        wrapped_rows = [formatted_values]
    else:
        wrapped_rows = []
        for row_idx in range(max_rows):
            row = []
            for col_idx in range(col_count):
                col = all_col_lines[col_idx]
                col_def = col_defs[col_idx]
                if row_idx < len(col):
                    text = col[row_idx]
                else:
                    text = ''
                text = col_def.format_text(text)
                row.append(text)
            wrapped_rows.append(row)

    padding = ' ' * style.cell_padding
    if is_header:
        delim = padding + style.header_delimiter + padding
        left = style.header_left + padding
        right = '' if lazy_end else padding + style.header_right
    else:
        delim = padding + style.values_delimiter + padding
        left = style.values_left + padding
        right = '' if lazy_end else padding + style.values_right

    final_rows = []
    for row in wrapped_rows:
        row_text = left + delim.join(row) + right
        if lazy_end:
            row_text = row_text.rstrip()
        final_rows.append(row_text)

    return '\n'.join(final_rows)


def get_table_row(values: List[str],
                  style: TableStyle = NoBorderScreenStyle(),
                  col_defs: List[str|ColDef] = None,
                  table_width: int = None,
                  lazy_end: bool = True) -> str:

    return _get_table_row(values=values,
                          style=style,
                          col_defs=col_defs,
                          table_width=table_width,
                          lazy_end=lazy_end,
                          is_header=False)


###############################################################################
# get_table_header
###############################################################################

def get_table_header(header_cols: List[str],
                     style: TableStyle = NoBorderScreenStyle(),
                     header_defs: List[str|ColDef] = None,
                     col_defs: List[str|ColDef] = None,
                     table_width: int = None,
                     lazy_end: bool = True) -> str:
    if not table_width and style.terminal_style:
        table_width = get_term_width()
    if not header_defs:
        header_defs = _get_col_defs_for_table([header_cols])
    else:
        _parse_col_defs(header_defs)
    _adjust_col_defs(header_defs, [header_cols], table_width, style)

    if not col_defs:
        col_defs = header_defs.copy()

    lazy_end = lazy_end and style.allow_lazy_header

    lines = []
    if style.top_border:
        line = style.header_top_line
        delim = style.header_top_delimiter
        left = style.header_top_left
        right = line if lazy_end else style.header_top_right
        border_lines = [line * (col.width + 2) for col in col_defs]
        border = delim.join(border_lines)
        border = left + border + right
        lines.append(border)

    headers = _get_table_row(values=header_cols,
                             style=style,
                             col_defs=header_defs,
                             table_width=table_width,
                             lazy_end=lazy_end,
                             is_header=True)
    lines.append(headers)

    line = style.header_bottom_line
    delim = style.header_bottom_delimiter
    left = style.header_bottom_left
    right = line if lazy_end else style.header_bottom_right
    border_lines = []
    for col_idx in range(len(header_cols)):
        header_def = header_defs[col_idx]
        col_def = None
        if col_idx < len(col_defs):
            col_def = col_defs[col_idx]
        if not style.align_char:
            h_line = line * (header_def.width + 2)
        else:
            h_line = line * header_def.width
            if col_def and col_def.align == '^':
                h_line = style.align_char + h_line + style.align_char
            elif col_def and col_def.align == ">":
                h_line = ' ' + h_line + style.align_char
            else:
                h_line = ' ' + h_line + ' '
        border_lines.append(h_line)
    border = delim.join(border_lines)
    border = left + border + right
    lines.append(border)

    return '\n'.join(lines)

###############################################################################
# get_table
###############################################################################

def get_table(value_rows: List[List[str]],
              header_row: List[str] = None,
              style: TableStyle = NoBorderScreenStyle(),
              col_defs: List[str|ColDef] = None,
              header_defs: List[str|ColDef] = None,
              table_width: int = None,
              lazy_end: bool = False) -> str:

    if not value_rows:
        return get_table([["No data to display"]], style=style, table_width=table_width, lazy_end=lazy_end)

    if not table_width and style.terminal_style:
        table_width = get_term_width()

    all_rows = value_rows.copy()
    if header_row:
        all_rows.insert(0, header_row.copy())

    if not col_defs:
        col_defs = _get_col_defs_for_table(all_rows)
    else:
        _parse_col_defs(col_defs)
    _adjust_col_defs(col_defs, all_rows, table_width, style)

    if not header_row and style.force_header:
        header_row = [''] * len(col_defs)

    if header_row:
        real_header_defs: List[ColDef] = []
        for col_def in col_defs:
            real_header_defs.append(ColDef(
                width=col_def.width,
                align='^'
            ))
        # if the defs are supplied, we only support alignment
        if header_defs:
            _parse_col_defs(header_defs)
            for col_idx in range(len(col_defs)):
                if col_idx < len(header_defs):
                    header_def = header_defs[col_idx]
                    if header_def.align:
                        real_header_defs[col_idx].align = header_def.align

    # Generate header and rows
    output_rows = []
    if header_row:
        row = get_table_header(header_cols=header_row,
                               style=style,
                               header_defs=real_header_defs,
                               col_defs=col_defs,
                               table_width=table_width,
                               lazy_end=lazy_end)
        output_rows.append(row)
    else:
        if style.top_border:
            line = style.no_header_top_line
            delim = style.no_header_top_delimiter
            left = style.no_header_top_left
            right = line if lazy_end else style.no_header_top_right
            border_lines = [line * (col.width + 2) for col in col_defs]
            border = delim.join(border_lines)
            border = left + border + right
            output_rows.append(border)

    for values in value_rows:
        row = get_table_row(values=values,
                            style=style,
                            col_defs=col_defs,
                            table_width=table_width,
                            lazy_end=lazy_end)
        output_rows.append(row)

    if style.bottom_border:
        line = style.values_bottom_line
        delim = style.values_bottom_delimiter
        left = style.values_bottom_left
        right = line if lazy_end else style.values_bottom_right
        border_lines = [line * (col.width + 2) for col in col_defs]
        border = delim.join(border_lines)
        border = left + border + right
        output_rows.append(border)

    return '\n'.join(output_rows)

if __name__ == "__main__":
    t1 = [
        ['abc', '123', '123 123 123'],
        ['abc', '123 123', '123 123 123 123'],
        ['abc', '123', '123 123 123 123 123'],
        ['abc', '123 123', '123 123'],
    ]
    t1_head = ['col 1','col 2','col 3']
    t2 = [
        ['a', '123', '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'
                     '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'],
        ['a', '123', '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'
                     '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'],
        ['a', '123', '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'
                     '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'],
        ['a', '123', '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'
                     '123 123 123 123 123 123 123 123 123 123 123 123 123 123 123'],
    ]
    t3 = [
        ['This is a line','This is a line that already has newlines in it.\n'
                          '  * will it wrap?\n'
                          '  * will it indent properly?'],
        ['This is a line','This is a line that already has newlines in it.\n'
                          '  * will it wrap?\n'
                          '  * will it indent properly?'],
        ['This is a line','This is a line that already has newlines in it.\n'
                          '  * will it wrap?\n'
                          '  * will it indent properly?'],
    ]

    print(get_table(t1))
    print(get_table(t1,t1_head))
    print(get_table(t2))

    print(get_table(t1, style=BasicScreenStyle(), lazy_end=True))
    print(get_table(t1,t1_head, style=BasicScreenStyle(), col_defs=['10','^10T','>30']))
    print(get_table(t2, style=BasicScreenStyle(), col_defs=['10','^10','30T']))
    print(get_table(t2, style=BasicScreenStyle(), col_defs=['10','^10','70']))
    print(get_table(t2, style=BasicScreenStyle(), col_defs=['','^','>A'], table_width=50))

    print(get_table(t1, style=MarkdownStyle(), lazy_end=True))
    print(get_table(t1,t1_head, style=MarkdownStyle(), col_defs=['','^','']))
    print(get_table(t1,t1_head, style=MarkdownStyle(), col_defs=['','^',''], header_defs=['','','<']))
    print(get_table(t2, style=MarkdownStyle(), table_width=80))
    print(get_table(t2, style=MarkdownStyle(), lazy_end=True))

    print(get_table(t3))
    print(get_table(t3, table_width=50))
