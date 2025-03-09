# Interactive tests only
if __name__ == "__main__":

    from f_table import (
        get_table,
        BasicScreenStyle,
        MarkdownStyle,
        NoBorderScreenStyle,
        RoundedBorderScreenStyle,
    )

    def l():
        print("\n" + "*" * 80 + "\n")

    variable_table = [
        ["abc", "123", "123 123 123"],
        ["abc", "123 123", "123 123 123 123"],
        ["abc", "123", "123 123 123 123 123"],
        ["abc", "123 123", "123 123"],
    ]
    variable_table_head = ["col 1", "col 2", "col 3"]

    wrapping_table = [
        [
            "a",
            "123",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
            "sed do eiusmod tempor incididunt ut labore et dolore magna "
            "aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
            "ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        ],
        [
            "a",
            "123",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
            "sed do eiusmod tempor incididunt ut labore et dolore magna "
            "aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
            "ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        ],
    ]

    embedded_newline_table = [
        [
            "This is a line",
            "This is a line that already has newlines in it.\n"
            "  * will it wrap?\n"
            "  * will it indent properly?",
        ],
        [
            "This is a line",
            "This is a line that already has newlines in it.\n"
            "  * will it wrap?\n"
            "  * will it indent properly?",
        ],
        [
            "This is a line",
            "This is a line that already has newlines in it.\n"
            "  * will it wrap?\n"
            "  * will it indent properly?",
        ],
    ]
    embedded_newline_table_head = ["LINE", "LINE WITH NEWLINES"]

    print(get_table(variable_table))
    l()
    print(get_table(variable_table, variable_table_head))
    l()
    print(get_table(wrapping_table))
    l()

    print(get_table(variable_table, style=BasicScreenStyle(), lazy_end=True))
    l()
    print(
        get_table(
            variable_table,
            variable_table_head,
            style=BasicScreenStyle(),
            col_defs=["10", "^10T", ">30"],
        )
    )
    l()
    print(
        get_table(
            wrapping_table, style=BasicScreenStyle(), col_defs=["10", "^10", "30T"]
        )
    )
    l()
    print(
        get_table(
            wrapping_table, style=BasicScreenStyle(), col_defs=["10", "^10", "70"]
        )
    )
    l()
    print(
        get_table(
            wrapping_table,
            style=BasicScreenStyle(),
            col_defs=["", "^", ">A"],
            table_width=50,
        )
    )
    l()

    print(get_table(variable_table, style=MarkdownStyle(), lazy_end=True))
    l()
    print(
        get_table(
            variable_table,
            variable_table_head,
            style=MarkdownStyle(),
            col_defs=["", "^", ""],
        )
    )
    l()
    print(
        get_table(
            variable_table,
            variable_table_head,
            style=MarkdownStyle(),
            col_defs=["", "^", ""],
            header_defs=["", "", "<"],
        )
    )
    l()
    print(get_table(wrapping_table, style=MarkdownStyle(), table_width=80))
    l()
    print(get_table(wrapping_table, style=MarkdownStyle(), lazy_end=True))
    l()

    print(get_table(embedded_newline_table))
    l()
    print(get_table(embedded_newline_table, table_width=50))
    l()
    print(get_table(embedded_newline_table, style=NoBorderScreenStyle()))
    l()
    print(get_table(embedded_newline_table, style=RoundedBorderScreenStyle()))
    l()
    print(
        get_table(
            embedded_newline_table,
            header_row=embedded_newline_table_head,
            style=RoundedBorderScreenStyle(),
            separete_rows=True,
        )
    )
    l()
