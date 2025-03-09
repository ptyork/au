import click
import pathlib

BASE_PATH_KEY = "au.base_path"


class BasePathType(click.Path):
    def __init__(self, exists=True, resolve_path=False, allow_dash=False):
        super().__init__(
            exists=exists,
            file_okay=False,
            dir_okay=True,
            path_type=pathlib.Path,
            resolve_path=resolve_path,
            allow_dash=allow_dash,
        )

    def convert(self, value, param, ctx):
        converted_value = super().convert(value, param, ctx)
        if isinstance(converted_value, pathlib.Path):
            ctx.meta[BASE_PATH_KEY] = converted_value.resolve()
            return converted_value
        return converted_value
