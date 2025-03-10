import click
import sys
import functools
import logging
from pathlib import Path

from au.classroom import AssignmentSettings, Roster
from au.common import select_file
from .BasePathType import BASE_PATH_KEY

logger = logging.getLogger(__name__)


class RosterOptions:
    def __init__(
        self,
        load: bool = True,
        store: bool = True,
        prompt=False,
        required=False,
    ):
        self.load = load
        self.store = store
        self.prompt = prompt
        self.required = required

    def _get_settings(self, base_path):
        if base_path and (self.load or self.store):
            try:
                return AssignmentSettings.get_classroom_settings(base_path)
            except:
                if self.store:
                    if AssignmentSettings.is_valid_settings_path(base_path):
                        return AssignmentSettings(base_path, create=True)
        elif self.load or self.store:
            logger.error(
                "RosterOptions can't be used with store or load if an argument of type BasePath is not also included."
            )
            sys.exit(1)
        return None

    def options(self, func):
        help_text = (
            "A GitHub Classroom roster file, typically named `classroom_roster.csv`."
        )
        if self.load:
            help_text += (
                " If not provided, will try to read a value stored in settings."
            )
        if self.prompt:
            help_text += " Will prompt for the file if not provided."
        if self.required:
            help_text += " A roster is REQUIRED to run this command."

        @click.option(
            "--roster",
            type=click.Path(dir_okay=False, exists=True, path_type=Path),
            help=help_text,
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ctx = click.get_current_context()
            base_path = ctx.meta.get(BASE_PATH_KEY)  # Command must use BasePath type
            settings = self._get_settings(base_path)
            roster_file: Path = None
            if "roster" in kwargs:
                roster_file = kwargs.get("roster")
            kwargs["roster"] = None  # replace with the actual roster if found
            if self.load and not roster_file:
                if settings and settings.roster_file:
                    roster_file = settings.roster_file
            if not roster_file and self.prompt:
                optional = ""
                if not self.required:
                    optional = " (Press esc for none)"
                roster_file = select_file(
                    title=f"CHOOSE ROSTER CSV FILE{optional}",
                    root=base_path,
                    filter="*.csv",
                )
                if roster_file:
                    click.echo(f" > CHOICE: {roster_file}")
                else:
                    click.echo(" X CHOICE: NONE")
            if not roster_file and self.required:
                click.echo("A roster is required for this operation.\n")
                click.echo(click.get_current_context().get_help())
                sys.exit(1)
            if roster_file:
                try:
                    roster = Roster(roster_file)
                    kwargs["roster"] = roster
                except:
                    logger.exception("Error encountered while processing roster")
                    sys.exit(1)
                try:
                    if settings and self.store:
                        with settings:
                            settings.roster_file = roster_file
                except Exception:
                    logger.exception("Error encountered while writing settings")
            return func(*args, **kwargs)

        return wrapper
