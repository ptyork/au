import click
import sys
import functools
import logging

from au.classroom import ClassroomSettings
from au.classroom import Assignment, Classroom, choose_assignment, choose_classroom, get_assignment

logger = logging.getLogger(__name__)

class AssignmentOptions:
    def __init__(self, load: bool = True, store: bool = True):
        self.load = load
        self.store = store

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
        return None
            
    def options(self, func):
        help_text = "The integer classroom id for the assignment."
        if self.load:
            help_text += " If not provided, will attempt to find a value in the local classroom settings file. Will prompt for it interactively if not found."
        else:
            help_text += " Will prompt for it interactively if not found provided."

        @click.option("--assignment-id", type=int, help=help_text)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            settings = self.get_settings()
            assignment_id: int = None
            if "assignment_id" in kwargs:
                assignment_id = kwargs.pop('assignment_id')
            if self.load and not assignment_id:
                if settings and settings.assignment_id:
                    assignment_id = settings.assignment_id
            if assignment_id:
                assignment = get_assignment(assignment_id)
            else:
                classroom: Classroom = choose_classroom()
                assignment: Assignment = choose_assignment(classroom)
            if assignment:
                kwargs['assignment'] = assignment
                try:
                    if settings and self.store:
                        with settings:
                            settings.classroom_id = assignment.classroom.id
                            settings.assignment_id = assignment.id
                except Exception:
                    logger.exception("Error encountered while writing settings")
            elif assignment_id:
                logger.error(f"Unable to find assignment with id = {assignment_id}")
                sys.exit(1)
            return func(*args, **kwargs)
        
        return wrapper
