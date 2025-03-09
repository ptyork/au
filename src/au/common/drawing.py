from enum import Enum

DEFAULT_LINE_WIDTH = 100


class BoxChars(Enum):
    """Unicode box drawing characters."""

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


def get_single_line(text: str = "", width: int = DEFAULT_LINE_WIDTH) -> str:
    get_line(BoxChars.HEAVY_HORIZONTAL, text, width)


def get_double_line(text: str = "", width: int = DEFAULT_LINE_WIDTH) -> str:
    get_line(BoxChars.DOUBLE_HORIZONTAL, text, width)


def get_line(
    char: str = BoxChars.HEAVY_HORIZONTAL,
    text: str = "",
    width: int = DEFAULT_LINE_WIDTH,
) -> str:
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
