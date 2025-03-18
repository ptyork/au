from typing import Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pprint import pformat

from f_table import get_table

from au.common.datetime import get_friendly_local_datetime

from .gh import github_json_serializer


def _as_json(obj):
    dct = asdict(obj)
    return json.dumps(dct, default=github_json_serializer)


@dataclass
class Organization:
    id: int
    login: str
    node_id: Optional[str]
    html_url: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]

    def as_table(self) -> str:
        return get_table(
            [
                ["Organization Login", self.login],
                ["Organization ID", self.id],
                ["Organization Name", self.name],
                ["Organization Node ID", self.node_id],
                ["Organization HTML URL", self.html_url],
                ["Organization Avatar URL", self.avatar_url],
            ],
            col_defs=["25", ""],
        )

    def __str__(self):
        return self.as_table()


@dataclass
class Classroom:
    id: int
    name: str
    url: str
    archived: bool
    organization: Optional[Organization]

    def as_table(self) -> str:
        table = get_table(
            [
                ["Classroom Name", self.name],
                ["Classroom ID", self.id],
                ["Classroom URL", self.url],
                ["Classroom is Archived", self.archived],
            ],
            col_defs=["25", ""],
        )
        if self.organization:
            table += "\n" + self.organization.as_table()
        return table

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return get_table(
            [
                ["Classroom Name", self.name],
                ["Classroom ID", self.id],
            ],
            col_defs=["25", ""],
        )


@dataclass
class Repository:
    id: int
    name: str
    full_name: str
    html_url: str
    node_id: str
    private: bool
    default_branch: str

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return pformat(self)


@dataclass
class Assignment:
    id: int
    title: str
    slug: Optional[str]
    deadline: Optional[datetime]
    accepted: Optional[int]
    submissions: Optional[int]
    passing: Optional[int]
    invite_link: Optional[str]
    type: Optional[str]
    editor: Optional[str]
    public_repo: Optional[bool]
    invitations_enabled: Optional[bool]
    students_are_repo_admins: Optional[bool]
    feedback_pull_requests_enabled: Optional[bool]
    max_teams: Optional[int]
    max_members: Optional[int]
    language: Optional[str]
    classroom: Optional[Classroom]
    starter_code_repository: Optional[Repository]

    def as_table(self) -> str:
        table = get_table(
            [
                ["Classroom Name", self.classroom.name],
                ["Classroom ID", self.classroom.id],
                ["Assignment Title", self.title],
                ["Short Name (slug)", self.slug],
                ["Assignment ID", self.id],
                ["Assignment Deadline", get_friendly_local_datetime(self.deadline)],
                ["Assignment Type", self.type],
                ["Assignment Editor", self.editor],
                ["Assignment is Public", self.public_repo],
                ["Number Accepted", self.accepted],
                ["Number Submitted", self.submissions],
                ["Number Passing", self.passing],
            ],
            col_defs=["25", ""],
        )
        return table

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        table = get_table(
            [
                ["Assignment Title", self.title],
                ["Assignment ID", self.id],
                ["Deadline", get_friendly_local_datetime(self.deadline)],
            ],
            col_defs=["25", ""],
        )
        if self.classroom:
            table = str(self.classroom) + "\n" + table
        return table


@dataclass
class Student:
    id: int
    login: str
    name: Optional[str]
    avatar_url: str
    html_url: str

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return pformat(self)


@dataclass
class AcceptedAssignment:
    id: int
    submitted: bool
    passing: bool
    commit_count: int
    grade: Optional[str]
    students: List[Student]
    assignment: Assignment
    repository: Repository

    @property
    def login(self):
        if not self.students:
            return None
        else:
            return self.students[0].login

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return pformat(self)
