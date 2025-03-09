from enum import Enum


class BoxChars(Enum):
    """Unicode box drawing characters"""

    LIGHT_HORIZONTAL = "\u2500"
    HEAVY_HORIZONTAL = "\u2501"
    LIGHT_VERTICAL = "\u2502"
    HEAVY_VERTICAL = "\u2503"
    LIGHT_DOWN_AND_RIGHT = "\u250c"
    HEAVY_DOWN_AND_RIGHT = "\u250f"
    LIGHT_DOWN_AND_LEFT = "\u2510"
    HEAVY_DOWN_AND_LEFT = "\u2513"
    LIGHT_UP_AND_RIGHT = "\u2514"
    HEAVY_UP_AND_RIGHT = "\u2517"
    LIGHT_UP_AND_LEFT = "\u2518"
    HEAVY_UP_AND_LEFT = "\u251b"
    LIGHT_VERTICAL_AND_RIGHT = "\u251c"
    HEAVY_VERTICAL_AND_RIGHT = "\u2523"
    LIGHT_VERTICAL_AND_LEFT = "\u2524"
    HEAVY_VERTICAL_AND_LEFT = "\u252b"
    LIGHT_DOWN_AND_HORIZONTAL = "\u252c"
    HEAVY_DOWN_AND_HORIZONTAL = "\u2533"
    LIGHT_UP_AND_HORIZONTAL = "\u2534"
    HEAVY_UP_AND_HORIZONTAL = "\u253b"
    LIGHT_VERTICAL_AND_HORIZONTAL = "\u253c"
    HEAVY_VERTICAL_AND_HORIZONTAL = "\u254b"
    LIGHT_DOUBLE_DASH_HORIZONTAL = "\u254c"
    HEAVY_DOUBLE_DASH_HORIZONTAL = "\u254d"
    LIGHT_DOUBLE_DASH_VERTICAL = "\u254e"
    HEAVY_DOUBLE_DASH_VERTICAL = "\u254f"
    DOUBLE_HORIZONTAL = "\u2550"
    DOUBLE_VERTICAL = "\u2551"
    DOUBLE_DOWN_AND_RIGHT = "\u2554"
    DOUBLE_DOWN_AND_LEFT = "\u2557"
    DOUBLE_UP_AND_RIGHT = "\u255a"
    DOUBLE_UP_AND_LEFT = "\u255d"
    DOUBLE_VERTICAL_AND_RIGHT = "\u2560"
    DOUBLE_VERTICAL_AND_LEFT = "\u2563"
    DOUBLE_DOWN_AND_HORIZONTAL = "\u2566"
    DOUBLE_UP_AND_HORIZONTAL = "\u2569"
    DOUBLE_VERTICAL_AND_HORIZONTAL = "\u256c"
    DOUBLE_VERTICAL_AND_HEAVY_RIGHT = "\u2561"
    DOUBLE_VERTICAL_AND_HEAVY_LEFT = "\u2562"
    DOUBLE_DOWN_AND_HEAVY_HORIZONTAL = "\u2564"
    DOUBLE_UP_AND_HEAVY_HORIZONTAL = "\u2567"
    DOUBLE_VERTICAL_AND_HEAVY_HORIZONTAL = "\u256a"
    LIGHT_VERTICAL_AND_DOUBLE_RIGHT = "\u255f"
    LIGHT_VERTICAL_AND_DOUBLE_LEFT = "\u2562"
    LIGHT_DOWN_AND_DOUBLE_HORIZONTAL = "\u2565"
    LIGHT_UP_AND_DOUBLE_HORIZONTAL = "\u2568"
    LIGHT_VERTICAL_AND_DOUBLE_HORIZONTAL = "\u256b"
    LIGHT_ARC_DOWN_AND_RIGHT = "\u256d"
    LIGHT_ARC_DOWN_AND_LEFT = "\u256e"
    LIGHT_ARC_UP_AND_LEFT = "\u256f"
    LIGHT_ARC_UP_AND_RIGHT = "\u2570"
    HEAVY_ARC_DOWN_AND_RIGHT = "\u2571"
    HEAVY_ARC_DOWN_AND_LEFT = "\u2572"
    HEAVY_ARC_UP_AND_LEFT = "\u2573"
    HEAVY_ARC_UP_AND_RIGHT = "\u2574"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


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

        self.no_header_top_line = BoxChars.LIGHT_HORIZONTAL
        self.no_header_top_delimiter = BoxChars.LIGHT_DOWN_AND_HORIZONTAL
        self.no_header_top_left = BoxChars.LIGHT_DOWN_AND_RIGHT
        self.no_header_top_right = BoxChars.LIGHT_DOWN_AND_LEFT

        self.header_top_line = BoxChars.LIGHT_HORIZONTAL
        self.header_top_delimiter = BoxChars.LIGHT_DOWN_AND_HORIZONTAL
        self.header_top_left = BoxChars.LIGHT_DOWN_AND_RIGHT
        self.header_top_right = BoxChars.LIGHT_DOWN_AND_LEFT

        self.header_delimiter = BoxChars.LIGHT_VERTICAL
        self.header_left = BoxChars.LIGHT_VERTICAL
        self.header_right = BoxChars.LIGHT_VERTICAL

        self.header_bottom_line = BoxChars.LIGHT_HORIZONTAL
        self.header_bottom_delimiter = BoxChars.LIGHT_VERTICAL_AND_HORIZONTAL
        self.header_bottom_left = BoxChars.LIGHT_VERTICAL_AND_RIGHT
        self.header_bottom_right = BoxChars.LIGHT_VERTICAL_AND_LEFT

        self.values_delimiter = BoxChars.LIGHT_VERTICAL
        self.values_left = BoxChars.LIGHT_VERTICAL
        self.values_right = BoxChars.LIGHT_VERTICAL

        self.values_bottom_line = BoxChars.LIGHT_HORIZONTAL
        self.values_bottom_delimiter = BoxChars.LIGHT_UP_AND_HORIZONTAL
        self.values_bottom_left = BoxChars.LIGHT_UP_AND_RIGHT
        self.values_bottom_right = BoxChars.LIGHT_UP_AND_LEFT

        self.row_separator_line = "◦"
        self.row_separator_delimiter = BoxChars.LIGHT_VERTICAL
        self.row_separator_left = BoxChars.LIGHT_VERTICAL
        self.row_separator_right = BoxChars.LIGHT_VERTICAL


class BasicScreenStyle(TableStyle): ...


class RoundedBorderScreenStyle(TableStyle):
    def __init__(self):
        super().__init__()
        self.header_top_left = BoxChars.LIGHT_ARC_DOWN_AND_RIGHT
        self.header_top_right = BoxChars.LIGHT_ARC_DOWN_AND_LEFT
        self.no_header_top_left = BoxChars.LIGHT_ARC_DOWN_AND_RIGHT
        self.no_header_top_right = BoxChars.LIGHT_ARC_DOWN_AND_LEFT
        self.values_bottom_left = BoxChars.LIGHT_ARC_UP_AND_RIGHT
        self.values_bottom_right = BoxChars.LIGHT_ARC_UP_AND_LEFT


class NoBorderScreenStyle(TableStyle):
    def __init__(self):
        super().__init__()
        self.top_border = False
        self.bottom_border = False
        self.header_left = ""
        self.header_right = ""
        self.header_bottom_left = ""
        self.header_bottom_right = ""
        self.values_left = ""
        self.values_right = ""
        self.values_bottom_left = ""
        self.values_bottom_right = ""
        self.row_separator_line = "◦"
        self.row_separator_left = ""
        self.row_separator_right = ""


class MarkdownStyle(TableStyle):
    def __init__(self):
        super().__init__()
        self.top_border = False
        self.bottom_border = False
        self.terminal_style = False
        self.allow_lazy_header = False
        self.force_header = True
        self.align_char = ":"

        self.min_width = 3

        self.header_delimiter = "|"
        self.header_left = "|"
        self.header_right = "|"

        self.header_bottom_line = "-"
        self.header_bottom_delimiter = "|"
        self.header_bottom_left = "|"
        self.header_bottom_right = "|"

        self.values_delimiter = "|"
        self.values_left = "|"
        self.values_right = "|"

        self.row_separator_line = ""
        self.row_separator_delimiter = ""
        self.row_separator_left = ""
        self.row_separator_right = ""
