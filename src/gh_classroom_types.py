from dataclasses import dataclass, asdict
from datetime import date, datetime
import json

from datetime_util import utc_to_local

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

    def as_json(self) -> str:
        return _as_json(self)
    
    @staticmethod
    def from_json(json_str) -> 'Assignment':
        dct = json.loads(json_str, object_hook=_github_json_deserializer)
        return Assignment(dct['id'], dct['title'], dct['deadline'])
