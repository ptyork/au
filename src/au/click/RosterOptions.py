
import click
import sys
import functools
import logging
from pathlib import Path

from au.classroom import ClassroomSettings, Roster
from .BasePathType import BASE_PATH_KEY

logger = logging.getLogger(__name__)

class RosterOptions:
    def __init__(self, load: bool = True, store: bool = True, prompt = False, required=False):
        self.load = load
        self.store = store
        self.prompt = prompt
        self.required = required

    def get_settings(self):
        ctx = click.get_current_context()
        base_path = ctx.meta.get('au.base_path')    # Command must use BasePath type
        if base_path and (self.load or self.store):
            try:
                return ClassroomSettings.get_classroom_settings(base_path)
            except:
                if self.store:
                    if ClassroomSettings.is_valid_settings_path(base_path):
                        return  ClassroomSettings(base_path, create=True)
        elif self.load or self.store:
            logger.warning("RosterOptions can't be used with store or load if an argument of type BasePath is not also included.")
        return None
            
    def options(self, func):
        help_text = "A GitHub Classroom roster file, typically named `classroom_roster.csv`."
        if self.load:
            help_text += " If not provided, will attempt to find a value in the local classroom settings file."
        
        @click.option("--roster",
                      type=click.Path(dir_okay=False, exists=True, path_type=Path),
                      help=help_text)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            settings = self.get_settings()
            roster_file: Path = None
            if "roster" in kwargs:
                roster_file = kwargs.pop('roster')
            if self.load and not roster_file:
                if settings and settings.roster_file:
                    roster_file = settings.roster_file
            if not roster_file and self.prompt:
                roster_file = click.prompt("Enter path to roster file", type=Path, default=None)
            if not roster_file and self.required:
                click.echo("A roster is required for this operation.")
                click.echo(click.get_current_context().get_help())
                sys.exit(1)
            if roster_file:
                try:
                    roster = Roster(roster_file)
                    kwargs['roster'] = roster
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
