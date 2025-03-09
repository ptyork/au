from typing import Dict, List
from pathlib import Path
import logging
import re

from au.common import dict_from_csv


logger = logging.getLogger(__name__)

_invalid_name_char_pattern = re.compile(r'([<>:"\/\\\,|?*]|\s)+')


class Roster:
    def __init__(self, source: Path | List):
        if isinstance(source, Path):
            if source and source.exists():
                source = source.resolve()
                self.login_student_map: Dict[str, str] = dict_from_csv(
                    source, "github_username", "identifier"
                )
                for login in self.login_student_map:
                    if not self.login_student_map[login]:
                        self.login_student_map[login] = login
                self.file: Path = source
            else:
                raise FileNotFoundError(f"Roster file {source} not found.")
        elif isinstance(source, list):
            # source will be a list of logins or repository names, so just make the name and login the same
            self.login_student_map: Dict[str, str] = {str(v): str(v) for v in source}
        else:
            raise ValueError(str(source), "is not a valid roster source")

    def get_logins(self) -> List[str]:
        return list(self.login_student_map.keys())

    def get_names(self) -> List[str]:
        return list(self.login_student_map.values())

    def get_name(self, login: str) -> str:
        return self.login_student_map.get(login)

    def get_login_student_map(self):
        return self.login_student_map.copy()

    def get_student_login_map(self):
        student_login_map = {v: k for k, v in self.login_student_map.items()}
        if not len(self.login_student_map) == len(student_login_map):
            logger.warning("Duplicate student names found.")
        return student_login_map

    def append(self, login: str, name: str = None):
        """Add a login to the roster."""
        if login not in self.login_student_map:
            student = name if name else login
            self.login_student_map[login] = student

    def get_dir_names(self, prefix: str = None) -> Dict[str, str]:
        """Get friendly directory names for each student."""
        login_dir_name_map: Dict[str, str] = {}
        prefix = prefix if prefix else ""
        for login, student_name in self.login_student_map.items():
            if student_name != login:
                student_name = _invalid_name_char_pattern.sub("_", student_name)
                student_name = student_name.replace("__", "_")
                login_dir_name_map[login] = prefix + student_name + "@" + login
            else:
                login_dir_name_map[login] = prefix + login
        return login_dir_name_map

    @staticmethod
    def _get_dirs_from_source(
        dir_source: Path | List[any], sort_by_size=False
    ) -> List[str]:
        if isinstance(dir_source, Path):
            dirs: list[str] = []
            for subdir in dir_source.iterdir():
                # Only dirs
                if not subdir.is_dir():
                    continue
                # No hidden or special dirs
                if subdir.name[0] in "_.":
                    continue
                dirs.append(subdir.name)
        else:
            try:
                dirs = [d.name for d in dir_source]
            except:
                dirs = [str(d) for d in dir_source]

        if sort_by_size:
            dirs.sort(key=lambda l: len(l), reverse=True)
        else:
            dirs.sort()
        return dirs

    def get_login_dir_map(
        self, dir_source: Path | List[str], include_unmapped=False
    ) -> Dict[str, str | None]:
        """
        Map student logins to subdirectories or root_dir.

        In the rare case of multiple matches, only the first matching
        subdirectory is mapped.
        """
        logins = list(self.login_student_map.keys())
        logins.sort(key=lambda l: len(l), reverse=True)
        login_dir_map: Dict[str, str | None] = {}
        if include_unmapped:
            login_dir_map = {k: None for k in logins}
        subdirs = Roster._get_dirs_from_source(dir_source)
        for subdir in subdirs:
            for login in logins:
                if login in subdir and not login_dir_map.get(login):
                    login_dir_map[login] = subdir
                    break
        return login_dir_map

    def get_dir_login_map(self, dir_source: Path | List[str]) -> Dict[str, str | None]:
        """
        Map subdirectories of root_dir to student logins.

        In the rare case of multiple matches, all matching subdirectories
        will be mapped to a matching login.
        """
        subdirs = Roster._get_dirs_from_source(dir_source)
        dir_login_map: Dict[str, str | None] = {}
        logins = list(self.login_student_map.keys())
        logins.sort(key=lambda l: len(l), reverse=True)
        for subdir in subdirs:
            dir_login_map[subdir] = None
            for login in logins:
                if login in subdir:
                    dir_login_map[subdir] = login
        return dir_login_map

    def get_dir_student_map(
        self, dir_source: Path | List[str]
    ) -> Dict[str, str | None]:
        """
        Just a convenience method to map dirs directly to student names instead
        of logins.
        """
        dir_login_map = self.get_dir_login_map(dir_source)
        dir_student_map: Dict[str, str | None] = {}
        for dirname, login in dir_login_map.items():
            student = None
            if login:
                student = self.login_student_map[login]
            dir_student_map[dirname] = student
        return dir_student_map

    def get_login_for_dir(self, path: Path) -> str:
        dir_name = path.resolve().name
        logins = list(self.login_student_map.keys())
        logins.sort(key=lambda l: len(l), reverse=True)
        for login in logins:
            if login in dir_name:
                return login
        return None
