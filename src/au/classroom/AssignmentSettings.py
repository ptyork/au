from enum import Enum
from pathlib import Path
from au import SettingsBase
from git_wrap import has_git_repo_subdirs, GitRepo

from .AssignmentType import AssignmentType, assignment_types


# Classroom Settings Keys
_CLASSROOM_ID = "Classroom.classroom_id"
_ASSIGNMENT_ID = "Classroom.assignment_id"
_ASSIGNMENT_ID_OLD = "Assignment.assignment_id"  # Deprecated key
_ROSTER_FILE = "Classroom.roster_file"

# Assignment Settings Keys
_ASSIGNMENT_TYPE = "Assignment.assignment_type"
_SOLUTION_DIR = "Assignment.solution_dir"
_TEMPLATE_DIR = "Assignment.template_dir"
_SUBMISSION_DIR = "Assignment.submission_dir"


class AssignmentSettings(SettingsBase):
    FILENAME = "assignment.toml"

    def __init__(self, settings_doc_path: Path | str, create=False):
        path = Path(settings_doc_path)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        file = path / self.FILENAME
        super().__init__(file, create)

    # 
    # GITHUB CLASSROOM SETTINGS
    #

    ###########################################################################
    # CLASSROOM ID
    ###########################################################################
    @property
    def classroom_id(self) -> int | None:
        return self.get(_CLASSROOM_ID)

    @classroom_id.setter
    def classroom_id(self, value: int | None):
        self.set(_CLASSROOM_ID, value)

    ###########################################################################
    # ASSIGNMENT ID
    ###########################################################################
    @property
    def assignment_id(self) -> int | None:
        assignment_id = self.get(_ASSIGNMENT_ID)
        if assignment_id is None:
            # Check deprecated key
            assignment_id = self.get(_ASSIGNMENT_ID_OLD)
            if assignment_id is not None:
                # Migrate to new key
                self.set(_ASSIGNMENT_ID, assignment_id)
                self.delete(_ASSIGNMENT_ID_OLD)
        return assignment_id

    @assignment_id.setter
    def assignment_id(self, value: int | None):
        self.set(_ASSIGNMENT_ID, value)

    ###########################################################################
    # ROSTER FILE
    ###########################################################################
    @property
    def roster_file(self) -> Path | None:
        return self.get(_ROSTER_FILE, is_path=True)

    @roster_file.setter
    def roster_file(self, value: Path | None):
        self.set(_ROSTER_FILE, value)


    #
    # ASSIGNMENT SETTINGS
    #

    ###########################################################################
    # ASSIGNMENT TYPE
    ###########################################################################
    @property
    def assignment_type(self) -> AssignmentType | None:
        lang_str = self.get(_ASSIGNMENT_TYPE)
        if lang_str and lang_str in assignment_types:
            return assignment_types[lang_str]
        return None

    @assignment_type.setter
    def assignment_type(self, value: AssignmentType | str | None):
        if isinstance(value, AssignmentType):
            self.set(_ASSIGNMENT_TYPE, value.name)
        elif isinstance(value, str):
            type_ = assignment_types.get(value)
            if type_:
                self.set(_ASSIGNMENT_TYPE, type_.name)
            else:
                raise ValueError(f"Unknown assignment type: {value}")
        else:
            self.set(_ASSIGNMENT_TYPE, None)

    ###########################################################################
    # SOLUTION_DIR
    ###########################################################################
    @property
    def solution_dir(self) -> Path | None:
        return self.get(_SOLUTION_DIR, is_path=True)
    
    @solution_dir.setter
    def solution_dir(self, value: Path | None):
        self.set(_SOLUTION_DIR, value)

    ###########################################################################
    # TEMPLATE_DIR
    ###########################################################################
    @property
    def template_dir(self) -> Path | None:
        return self.get(_TEMPLATE_DIR, is_path=True)

    @template_dir.setter
    def template_dir(self, value: Path | None):
        self.set(_TEMPLATE_DIR, value)

    ###########################################################################
    # SUBMISSION_DIR
    ###########################################################################
    @property
    def submission_dir(self) -> Path | None:
        return self.get(_SUBMISSION_DIR, is_path=True)

    @submission_dir.setter
    def submission_dir(self, value: Path | None):
        self.set(_SUBMISSION_DIR, value)

    @staticmethod
    def is_valid_settings_path(path: Path) -> bool | None:
        """Returns True if this directory contains git repos. False if it IS a repo. None is indeterminate."""
        if GitRepo.is_repository_root(path):
            return False
        if has_git_repo_subdirs(path):
            return True
        return None

    @staticmethod
    def get_assignment_settings(
        settings_dir: Path | str, create: bool = False
    ) -> "AssignmentSettings":
        path = Path(settings_dir)
        try:
            return AssignmentSettings(path)
        except FileNotFoundError:
            try:
                return AssignmentSettings(path.parent)
            except FileNotFoundError:
                return AssignmentSettings(path, create=create)
