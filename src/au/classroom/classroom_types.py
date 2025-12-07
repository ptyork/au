from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pprint import pformat

from craftable import get_table

from au.common.datetime import get_friendly_local_datetime

from .gh import github_json_serializer


def _as_json(obj):
    dct = asdict(obj)
    return json.dumps(dct, default=github_json_serializer)


@dataclass(kw_only=True)
class Organization:
    id: int
    login: str
    node_id: str | None
    html_url: str | None
    name: str | None
    avatar_url: str | None

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


@dataclass(kw_only=True)
class Classroom:
    id: int
    name: str
    url: str
    archived: bool
    organization: Organization | None

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
            table += f"\n{self.organization.as_table()}"
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


@dataclass(kw_only=True)
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


@dataclass(kw_only=True)
class Assignment:
    id: int
    title: str
    slug: str | None
    deadline: datetime | None
    accepted: int | None
    submissions: int | None
    passing: int | None
    invite_link: str | None
    type: str | None
    editor: str | None
    public_repo: bool | None
    invitations_enabled: bool | None
    students_are_repo_admins: bool | None
    feedback_pull_requests_enabled: bool | None
    max_teams: int | None
    max_members: int | None
    language: str | None
    classroom: Classroom | None
    starter_code_repository: Repository | None

    def as_table(self) -> str:
        classroom_name = self.classroom.name if self.classroom else "N/A"
        classroom_id = self.classroom.id if self.classroom else "N/A"
        deadline = get_friendly_local_datetime(self.deadline) if self.deadline else "N/A"
        table = get_table(
            [
                ["Classroom Name", classroom_name],
                ["Classroom ID", classroom_id],
                ["Assignment Title", self.title],
                ["Short Name (slug)", self.slug],
                ["Assignment ID", self.id],
                ["Assignment Deadline", deadline],
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
        deadline = get_friendly_local_datetime(self.deadline) if self.deadline else "N/A"
        table = get_table(
            [
                ["Assignment Title", self.title],
                ["Assignment ID", self.id],
                ["Deadline", deadline],
            ],
            col_defs=["25", ""],
        )
        if self.classroom:
            table = f"{self.classroom}\n{table}"
        return table


@dataclass(kw_only=True)
class Student:
    id: int
    login: str
    name: str | None
    avatar_url: str
    html_url: str

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return pformat(self)


@dataclass(kw_only=True)
class AcceptedAssignment:
    id: int
    submitted: bool
    passing: bool
    commit_count: int
    grade: str | None
    students: list[Student]
    assignment: Assignment
    repository: Repository

    @property
    def login(self) -> str | None:
        if not self.students:
            return None
        else:
            return self.students[0].login

    def as_json(self) -> str:
        return _as_json(self)

    def __str__(self):
        return pformat(self)
