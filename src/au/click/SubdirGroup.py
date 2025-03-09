import click
import importlib
from pathlib import Path


class SubdirGroup(click.Group):
    def __init__(
        self, name=None, commands=None, file="", module="", cli_file="cli.py", **attrs
    ):
        self._file = file
        self._module = module
        self._cli_file = cli_file
        super().__init__(name, commands, **attrs)

    def list_commands(self, ctx: click.core.Context):
        rv = super().list_commands(ctx)
        module_dir = Path(self._file).parent
        for item in module_dir.iterdir():
            if item.is_dir() and item.name[0] not in "._":
                names = [f.name for f in item.iterdir()]
                if self._cli_file in names:
                    rv.append(item.name)
        rv.sort()
        return rv

    def get_command(self, ctx: click.core.Context, cmd_name: str):
        commands = self.list_commands(ctx)
        if cmd_name in commands:
            real_name = cmd_name
        else:
            matches = [x for x in commands if x.startswith(cmd_name)]
            if len(matches) != 1:
                return None
            real_name = matches[0]

        cmd = super().get_command(ctx, real_name)
        if cmd:
            return cmd
        else:
            try:
                mod = importlib.import_module(self._module + "." + real_name)
                return mod.cli.main
            except ImportError as ex:
                ctx.fail(f"Error importing tool module: {ex}")
                return None

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args
