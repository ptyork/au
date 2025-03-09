import click
import functools
import logging


class DebugOptions:
    def __init__(self, base_level=logging.INFO, quiet_level=logging.WARNING):
        self.base_level = base_level
        self.quiet_level = quiet_level

    def options(self, func):
        @click.option(
            "-d", "--debug", is_flag=True, help="set to enable detailed output"
        )
        @click.option(
            "-q", "--quiet", is_flag=True, help="set to reduce output to errors only"
        )
        @functools.wraps(func)
        def command_wrapper(*args, **kwargs):
            if kwargs.get("debug"):
                logging.getLogger().setLevel(logging.DEBUG)
            elif kwargs.get("quiet"):
                logging.getLogger().setLevel(self.quiet_level)
            else:
                logging.getLogger().setLevel(self.base_level)
            return func(*args, **kwargs)

        return command_wrapper
