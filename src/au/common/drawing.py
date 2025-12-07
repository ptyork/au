from craftable.styles import BoxChars

DEFAULT_LINE_WIDTH = 100


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
