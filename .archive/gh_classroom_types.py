from dataclasses import dataclass, asdict
from datetime import date, datetime
import json

from datetime_util import utc_to_local, get_friendly_local_datetime
from terminal_util import get_table_header, get_table_row
from terminal_util import get_md_table_header, get_md_table_row

# from typing import Annotated

def _github_json_serializer(obj):
    if isinstance(obj, (date, datetime)):
        dt = utc_to_local(obj)
        return dt.isoformat()
    raise TypeError(f"Type {type(obj)} not JSON serializable")

def _github_json_deserializer(dct):
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                dct[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                pass
    return dct

def _as_json(obj):
    dct = asdict(obj)
    return json.dumps(dct, default=_github_json_serializer)

@dataclass
class Course:
    id: int
    name: str
    # url: Annotated[str, 'Classroom URL']
    # org: Annotated[str, 'Login']
    # org_url: Annotated[str, "Organization URL"]

    def __str__(self):
        return f"""
Course Name :       {self.name}
Course ID :         {self.id}
                """.strip()

    def as_json(self) -> str:
        return _as_json(self)

    @staticmethod
    def from_json(json_str) -> 'Course':
        dct = json.loads(json_str, object_hook=_github_json_deserializer)
        return Course(dct['id'], dct['name'])


@dataclass
class Assignment:
    id: int
    title: str
    deadline: datetime = None
    # num_accepted: Annotated[int, 'Accepted']
    # num_submissions: Annotated[int, 'Submissions']
    # num_passing: Annotated[int, 'Passing']
    # invite_url: Annotated[str, 'Invite Link']
    # starter_url: Annotated[str, 'Starter Code Repo URL']
    # type: Annotated[str, 'Type']

    def __str__(self):
        return f"""
Assignment Title :  {self.title}
Assignment ID :     {self.id}
Deadline :          {get_friendly_local_datetime(self.deadline)}
                """.strip()


    def as_json(self) -> str:
        return _as_json(self)
    
    @staticmethod
    def from_json(json_str) -> 'Assignment':
        dct = json.loads(json_str, object_hook=_github_json_deserializer)
        return Assignment(dct['id'], dct['title'], dct['deadline'])


@dataclass
class AcceptedAssignment:
    id: int
    github_id: str
    repo_url: str
    commit_count: int
    # is_submitted: bool
    # is_passing: bool
    # grade: str
    # feedback_pull: str
    # request_url: str

    @staticmethod
    def print_header():
        header = get_md_table_header(
            ['ID','#CMIT','GITHUB ID','REPOSITORY'],
            [10,5,30,0],
            [1,0,-1,-1]
        )
        print(header)

    def __str__(self):
        text = get_md_table_row(
            [self.id, self.commit_count, self.github_id, self.repo_url],
            [10,5,30,0],
            [1,0,-1,-1]
        )
        return text

    def as_json(self) -> str:
        return _as_json(self)
    
    @staticmethod
    def from_json(json_str) -> 'Assignment':
        dct = json.loads(json_str, object_hook=_github_json_deserializer)
        return AcceptedAssignment(dct['id'], dct['github_id'], dct['repo_url'], dct['commit_count'])
