from typing import Iterator, List, Iterable, SupportsIndex, overload
from dataclasses import dataclass
import re
from textwrap import wrap

from .table_styles import TableStyle, NoBorderScreenStyle
from .terminal import get_term_width


class InvalidTableError(ValueError): ...


class InvalidColDefError(ValueError): ...


###############################################################################
# ColDef
###############################################################################

_FORMAT_SPEC_PATTERN = re.compile(
    r"((?P<fill>.)?(?P<align>[<>=^]))?"
    r"(?P<sign>[+\- ])?"
    r"(?P<alternate>[z#])?"
    r"(?P<zero>0)?"
    r"(?P<width>\d+)?"
    r"(?P<grouping_option>[_,])?"
    r"(?P<precision>\.\d+)?"
    r"(?P<type>[bcdeEfFgGnosxX%])?"
    r"(?P<table_config>[ANTS]+)?"
)


@dataclass
class ColDef:
    width: int | None = None
    align: str = "<"
    auto_fill: bool = False
    wrap: bool = True
    truncate: bool = False
    strict: bool = False
    _format_spec: str = ""

    def get_format_string(self) -> str:
        if self._format_spec:
            return f"{{:{self._format_spec}}}"
        else:
            return self.get_fallback_format_string()

    def get_fallback_format_string(self) -> str:
        return f"{{:{self.align}{self.width}}}"

    def format(self, value: any) -> str:
        # "Inner" format
        try:
            format_string = f"{{:{self._format_spec}}}"
            text = format_string.format(value)
        except:
            if self.strict:
                raise
            else:
                text = str(value)

        # "Outer" format
        return self.format_text(text)

    def format_text(self, text: str) -> str:
        if len(text) > self.width and self.truncate:
            text = text[: self.width - 1] + "…"

        if self.align == "^":
            text = text.strip().center(self.width)
        elif self.align == ">":
            text = text.strip().rjust(self.width)
        else:
            text = text.ljust(self.width)

        return text

    @staticmethod
    def parse(text) -> "ColDef":
        match = _FORMAT_SPEC_PATTERN.match(text)
        if not match:
            raise InvalidColDefError(f"Invalid format specifier for column: {text}")
        spec = match.groupdict()
        align = spec["align"]
        if not align or align == "=":
            align = ""
        width = spec["width"]
        if not width:
            width = None
        else:
            width = int(width)

        auto_size = False
        wrap_line = True
        truncate = False

        table_config = spec["table_config"]
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
            format_spec = ""
        except ValueError:
            pass

        return ColDef(
            width=width,
            align=align,
            auto_fill=auto_size,
            wrap=wrap_line,
            truncate=truncate,
            _format_spec=format_spec,
        )


###############################################################################
# ColDefList
###############################################################################


class ColDefList(list[ColDef]):
    """
    A list of ColDef objects.
    """

    def __init__(self, iterable: Iterable = []):
        super().__init__()
        for val in iterable:
            self.append(val)

    @overload
    def __setitem__(self, key: SupportsIndex, value: str | ColDef, /) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[str | ColDef], /) -> None: ...

    def __setitem__(self, key, value):
        if isinstance(key, SupportsIndex):
            if isinstance(value, str):
                super().__setitem__(key, ColDef.parse(value))
            elif isinstance(value, ColDef):
                super().__setitem__(key, value)
            else:
                raise ValueError("Column definition contain an invalid value")
        elif isinstance(key, slice) and isinstance(value, Iterable):
            values = ColDefList(value)
            super().__setitem__(key, values)
        else:
            raise ValueError("Column definitions contain an invalid value")

    @overload
    def __getitem__(self, i: SupportsIndex) -> ColDef: ...

    @overload
    def __getitem__(self, i: slice) -> "ColDefList": ...

    def __getitem__(self, i):
        result = super().__getitem__(i)
        if isinstance(i, slice):
            return ColDefList(result)
        else:
            return result

    def __iter__(self) -> Iterator[ColDef]:
        return super().__iter__()

    def append(self, object):
        if isinstance(object, str):
            super().append(ColDef.parse(object))
        elif isinstance(object, ColDef):
            super().append(object)
        else:
            raise ValueError("Column definitions contain an invalid value")

    def adjust_to_table(
        self,
        table_data: List[List[any]],
        table_width: int,
        style: TableStyle,
    ) -> None:
        # ADD MISSING COL DEFS
        max_cols = max([len(row) for row in table_data])
        diff = max_cols - len(self)
        if diff:
            for _ in range(diff):
                self.append(ColDef())

        # ADJUST WIDTHS OF FIELDS TO MATCH REALITY
        for col_idx in range(max_cols):
            max_width = max([len(str(row[col_idx])) for row in table_data])
            col_def = self[col_idx]
            if not col_def.width:
                col_def.width = max_width
            if col_def.width < style.min_width:
                col_def.width = style.min_width

        # ADJUST AUTO-FILL COLS TO FILL REMAINING SPACE AVAILABLE IN TOTAL TABLE_WIDTH
        if not table_width:
            return

        padding_len = style.cell_padding * 2 * len(self)
        border_len = len(str(style.values_left)) + len(str(style.values_right))
        delims_len = len(str(style.values_delimiter)) * (len(self) - 1)
        non_text_len = padding_len + border_len + delims_len
        total_len = non_text_len + sum([c.width for c in self])

        fill_cols = [col_idx for col_idx in range(len(self)) if self[col_idx].auto_fill]
        if not fill_cols:
            if total_len <= table_width:
                return
            else:
                largest_col = self[0]
                largest_col_idx = 0
                for col_idx in range(1, len(self)):
                    col_def = self[col_idx]
                    if col_def.width > largest_col.width:
                        largest_col = col_def
                        largest_col_idx = col_idx
                largest_col.auto_fill = True
                fill_cols.append(largest_col_idx)

        fixed_len = sum([c.width for c in self if not c.auto_fill])

        remaining_width = table_width - fixed_len - non_text_len
        fill_width = remaining_width // len(fill_cols)

        if fill_width < style.min_width:
            raise ValueError(
                "Unable to expand columns to fit table width because existing columns are too wide"
            )

        remainder = remaining_width % len(fill_cols)
        for col_idx in fill_cols:
            new_width = fill_width
            if remainder:
                new_width += 1
                remainder -= 1
            self[col_idx].width = new_width

    @staticmethod
    def assert_valid_table(table: any) -> int:
        if not isinstance(table, (list, tuple)):
            raise ValueError("Table data must be a list or tuple")
        for row in table:
            if not isinstance(row, (list, tuple)):
                raise ValueError("Each row in a table must be a list or tuple")
            for cell in row:
                if isinstance(cell, (list, tuple, dict)):
                    raise ValueError(
                        "Each cell in a table row must contain a single value (not a list, tuple or dict)."
                    )

    @staticmethod
    def for_table(table: List[List[any]]) -> "ColDefList":
        ColDefList.assert_valid_table(table)
        max_cols = max([len(row) for row in table])
        col_defs = ColDefList([ColDef() for _ in range(max_cols)])
        for col_idx in range(max_cols):
            max_width = 0
            for row in table:
                if col_idx < len(row):
                    max_width = max(max_width, len(str(row[col_idx])))
            col_defs[col_idx].width = max_width
        return col_defs


###############################################################################
# get_table_row
###############################################################################


def _get_table_row(
    values: List[str],
    style: TableStyle = NoBorderScreenStyle(),
    col_defs: List[str | ColDef] | ColDefList = None,
    table_width: int = None,
    lazy_end: bool = False,
    is_header: bool = False,
) -> str:
    if not table_width and style.terminal_style:
        table_width = get_term_width()

    if not col_defs:
        _col_defs = ColDefList.for_table([values])
    elif isinstance(col_defs, ColDefList):
        _col_defs = col_defs
    else:
        _col_defs = ColDefList(col_defs)
    _col_defs.adjust_to_table([values], table_width, style)

    col_count = len(values)

    formatted_values = []
    for col_idx in range(col_count):
        col_val = values[col_idx]
        col_def = _col_defs[col_idx]
        text = col_def.format(col_val)
        formatted_values.append(text)

    all_col_lines = []
    for col_idx in range(col_count):
        col_lines = []
        col_def = _col_defs[col_idx]
        text = formatted_values[col_idx]
        split = text.splitlines()
        if not split:
            split = [""]
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
                col_def = _col_defs[col_idx]
                if row_idx < len(col):
                    text = col[row_idx]
                else:
                    text = ""
                text = col_def.format_text(text)
                row.append(text)
            wrapped_rows.append(row)

    padding = " " * style.cell_padding
    if is_header:
        delim = padding + str(style.header_delimiter) + padding
        left = str(style.header_left) + padding
        right = "" if lazy_end else padding + str(style.header_right)
    else:
        delim = padding + str(style.values_delimiter) + padding
        left = str(style.values_left) + padding
        right = "" if lazy_end else padding + str(style.values_right)

    final_rows = []
    for row in wrapped_rows:
        row_text = left + delim.join(row) + right
        if lazy_end:
            row_text = row_text.rstrip()
        final_rows.append(row_text)

    return "\n".join(final_rows)


def get_table_row(
    values: List[str],
    style: TableStyle = NoBorderScreenStyle(),
    col_defs: List[str | ColDef] | ColDefList = None,
    table_width: int = None,
    lazy_end: bool = True,
) -> str:
    return _get_table_row(
        values=values,
        style=style,
        col_defs=col_defs,
        table_width=table_width,
        lazy_end=lazy_end,
        is_header=False,
    )


###############################################################################
# get_table_header
###############################################################################


def get_table_header(
    header_cols: List[str],
    style: TableStyle = NoBorderScreenStyle(),
    header_defs: List[str | ColDef] | ColDefList = None,
    col_defs: List[str | ColDef] | ColDefList = None,
    table_width: int = None,
    lazy_end: bool = True,
) -> str:
    if not table_width and style.terminal_style:
        table_width = get_term_width()

    if not header_defs:
        _header_defs = ColDefList.for_table([header_cols])
    elif isinstance(header_defs, ColDefList):
        _header_defs = header_defs
    else:
        _header_defs = ColDefList(header_defs)
    _header_defs.adjust_to_table([header_cols], table_width, style)

    if not col_defs:
        col_defs = _header_defs.copy()

    lazy_end = lazy_end and style.allow_lazy_header
    padding = 2 * style.cell_padding

    lines = []
    if style.top_border:
        line = str(style.header_top_line)
        delim = str(style.header_top_delimiter)
        left = str(style.header_top_left)
        right = line if lazy_end else str(style.header_top_right)
        border_lines = [line * (col.width + padding) for col in col_defs]
        border = delim.join(border_lines)
        border = left + border + right
        lines.append(border)

    headers = _get_table_row(
        values=header_cols,
        style=style,
        col_defs=_header_defs,
        table_width=table_width,
        lazy_end=lazy_end,
        is_header=True,
    )
    lines.append(headers)

    line = str(style.header_bottom_line)
    delim = str(style.header_bottom_delimiter)
    left = str(style.header_bottom_left)
    right = line if lazy_end else str(style.header_bottom_right)
    border_lines = []
    for col_idx in range(len(header_cols)):
        header_def = _header_defs[col_idx]
        col_def = None
        if col_idx < len(col_defs):
            col_def = col_defs[col_idx]
        if not style.align_char:
            h_line = line * (header_def.width + padding)
        else:
            h_line = line * header_def.width
            if col_def and col_def.align == "^":
                h_line = str(style.align_char) + h_line + str(style.align_char)
            elif col_def and col_def.align == ">":
                h_line = " " + h_line + str(style.align_char)
            else:
                h_line = " " + h_line + " "
        border_lines.append(h_line)
    border = delim.join(border_lines)
    border = left + border + right
    lines.append(border)

    return "\n".join(lines)


###############################################################################
# get_table
###############################################################################


def get_table(
    value_rows: List[List[str]],
    header_row: List[str] = None,
    style: TableStyle = NoBorderScreenStyle(),
    col_defs: List[str | ColDef] | ColDefList = None,
    header_defs: List[str | ColDef] | ColDefList = None,
    table_width: int = None,
    lazy_end: bool = False,
    separete_rows: bool = False,
) -> str:
    if not value_rows:
        return get_table(
            [["No data to display"]],
            style=style,
            table_width=table_width,
            lazy_end=lazy_end,
        )

    if not table_width and style.terminal_style:
        table_width = get_term_width()

    all_rows = value_rows.copy()
    if header_row:
        all_rows.insert(0, header_row.copy())

    if not col_defs:
        _col_defs = ColDefList.for_table(all_rows)
    elif isinstance(col_defs, ColDefList):
        _col_defs = col_defs
    else:
        _col_defs = ColDefList(col_defs)
    _col_defs.adjust_to_table(all_rows, table_width, style)

    if not header_row and style.force_header:
        header_row = [""] * len(_col_defs)

    # generate viable header definitions
    if header_row:
        real_header_defs = ColDefList()
        for col_def in _col_defs:
            real_header_defs.append(ColDef(width=col_def.width, align="^"))

        # if the defs are supplied, we only support alignment
        if header_defs:
            _header_defs = ColDefList(header_defs)
            for col_idx in range(len(_col_defs)):
                if col_idx < len(_header_defs):
                    header_def = _header_defs[col_idx]
                    if header_def.align:
                        real_header_defs[col_idx].align = header_def.align

    # Generate header and rows
    output_rows = []
    if header_row:
        row = get_table_header(
            header_cols=header_row,
            style=style,
            header_defs=real_header_defs,
            col_defs=_col_defs,
            table_width=table_width,
            lazy_end=lazy_end,
        )
        output_rows.append(row)
    else:
        if style.top_border:
            line = str(style.no_header_top_line)
            delim = str(style.no_header_top_delimiter)
            left = str(style.no_header_top_left)
            right = line if lazy_end else str(style.no_header_top_right)
            border_lines = [line * (col.width + 2) for col in _col_defs]
            border = delim.join(border_lines)
            border = left + border + right
            output_rows.append(border)

    rowcount = 0
    for values in value_rows:
        rowcount += 1
        lastrow = rowcount == len(value_rows)
        row = get_table_row(
            values=values,
            style=style,
            col_defs=_col_defs,
            table_width=table_width,
            lazy_end=lazy_end,
        )
        output_rows.append(row)
        if not lastrow and separete_rows and style.row_separator_line:
            sep_lines = []
            left = str(style.row_separator_left)
            right = line if lazy_end else str(style.row_separator_right)
            delim = str(style.row_separator_delimiter)
            padding = 2 * style.cell_padding
            for col_def in _col_defs:
                sep_line = str(style.row_separator_line) * (col_def.width + padding)
                sep_lines.append(sep_line)
            separator = delim.join(sep_lines)
            separator = left + separator + right
            output_rows.append(separator)

    if style.bottom_border:
        line = str(style.values_bottom_line)
        delim = str(style.values_bottom_delimiter)
        left = str(style.values_bottom_left)
        right = line if lazy_end else str(style.values_bottom_right)
        border_lines = [line * (col.width + 2) for col in _col_defs]
        border = delim.join(border_lines)
        border = left + border + right
        output_rows.append(border)

    return "\n".join(output_rows)
