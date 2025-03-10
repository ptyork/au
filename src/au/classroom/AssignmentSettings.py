from pathlib import Path
from au import SettingsBase
from git_wrap import has_git_repo_subdirs, GitRepo


_CLASSROOM_ID = "Classroom.classroom_id"
_ASSIGNMENT_ID = "Assignment.assignment_id"
_ROSTER_FILE = "Classroom.roster_file"


class AssignmentSettings(SettingsBase):
    FILENAME = "assignment.toml"

    def __init__(self, settings_doc_path: Path | str, create=False):
        path = Path(settings_doc_path)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        file = path / self.FILENAME
        super().__init__(file, create)

    @property
    def classroom_id(self) -> int:
        return self.get(_CLASSROOM_ID)

    @classroom_id.setter
    def classroom_id(self, value):
        self.set(_CLASSROOM_ID, value)

    @property
    def assignment_id(self) -> int:
        return self.get(_ASSIGNMENT_ID)

    @assignment_id.setter
    def assignment_id(self, value):
        self.set(_ASSIGNMENT_ID, value)

    @property
    def roster_file(self) -> Path:
        return self.get(_ROSTER_FILE, is_path=True)

    @roster_file.setter
    def roster_file(self, value):
        self.set(_ROSTER_FILE, value)

    @staticmethod
    def is_valid_settings_path(path: Path) -> bool | None:
        """Returns True if this directory contains git repos. False if it IS a repo. None is indeterminate."""
        if GitRepo.is_repository_root(path):
            return False
        if has_git_repo_subdirs(path):
            return True
        return None

    @staticmethod
    def get_classroom_settings(
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
