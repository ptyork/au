#!/usr/bin/env python3

from typing import List, Dict, overload

import subprocess
import json as json_module
from pprint import pformat

from dacite import from_dict

from .classroom_types import (
    Classroom,
    Assignment,
    AcceptedAssignment,
    _github_json_deserializer,
)
from au.common import draw_single_line, select_choice
from au.common.datetime import get_friendly_local_datetime, utc_min

import logging

logger = logging.getLogger(__name__)


def _gh_api(endpoint: str) -> Dict[str, any]:
    cmd = ["gh", "api", endpoint, "--paginate"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        json = json_module.loads(result.stdout, object_hook=_github_json_deserializer)
        if isinstance(json, dict):
            if json.get("message", "").upper() == "NOT FOUND":
                logger.error(f"Invalid GitHub API Endpoint: {endpoint}")
                return None
        logger.debug(f"Retrieved JSON: {pformat(json)}")
        return json
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.exception(f"Error trying to run `gh` command")
        return None
    except json_module.JSONDecodeError as ex:
        logger.exception(f"Invalid JSON output from `gh` command")
        return None


###############################################################################
# get_classrooms / get_classroom / choose_classrooms
###############################################################################


def get_classrooms(include_archived=False) -> List[Classroom]:
    classrooms: List[Classroom] = []

    rooms_d = _gh_api("classrooms")
    if not rooms_d:
        return []
    for room_d in rooms_d:
        try:
            classroom = from_dict(Classroom, room_d)
        except:
            logger.exception("Error converting Classroom")
            return None
        classrooms.append(classroom)
    if not include_archived:
        classrooms = [c for c in classrooms if not c.archived]
    return classrooms


def get_classroom(classroom_id: int) -> Classroom:
    room_d = _gh_api(f"classrooms/{classroom_id}")
    if not room_d:
        return None
    try:
        classroom = from_dict(Classroom, room_d)
    except:
        logger.exception("Error converting Classroom")
        return None
    return classroom


def choose_classroom(
    include_archived: bool = False, suppress_print: bool = False
) -> Classroom:
    classrooms = get_classrooms(include_archived=include_archived)
    classrooms.reverse()
    choices = [c.name for c in classrooms]
    choice = select_choice(choices, title="CHOOSE CLASSROOM")
    if choice is not None:
        if not suppress_print:
            print(" > CHOICE:", choices[choice])
        return classrooms[choice]
    else:
        if not suppress_print:
            print(" X CHOICE: NONE")
        return None


###############################################################################
# get_assignments / choose_assignment / get_assignment
###############################################################################


@overload
def get_assignments(classroom: int) -> List[Assignment]: ...


@overload
def get_assignments(classroom: Classroom) -> List[Assignment]: ...


def get_assignments(classroom: Classroom | int) -> List[Assignment]:
    if isinstance(classroom, Classroom):
        classroom_id = classroom.id
    elif isinstance(classroom, int):
        classroom_id = classroom
    else:
        raise ValueError("classroom must be either int or Classroom")

    assignments: List[Assignment] = []

    assignments_d = _gh_api(f"classrooms/{classroom_id}/assignments")
    if not assignments_d:
        return []
    for assn_d in assignments_d:
        try:
            assignment = from_dict(Assignment, assn_d)
        except:
            logger.exception("Error converting Assignment")
            return None
        assignments.append(assignment)
    return assignments


@overload
def choose_assignment(classroom: int) -> Assignment: ...


@overload
def choose_assignment(classroom: Classroom) -> Assignment: ...


def choose_assignment(
    classroom: Classroom | int, suppress_print: bool = False
) -> Assignment:
    if isinstance(classroom, Classroom):
        classroom_id = classroom.id
    elif isinstance(classroom, int):
        classroom_id = classroom
    else:
        raise ValueError("classroom must be either int or Classroom")

    assignments = get_assignments(classroom_id)
    assignments.sort(key=lambda a: a.deadline if a.deadline else utc_min())
    assignments.reverse()
    maxlen = max([len(a.title) for a in assignments])
    choices = [
        a.title.ljust(maxlen + 2) + "Due: " + get_friendly_local_datetime(a.deadline)
        for a in assignments
    ]
    choice = select_choice(choices, title="CHOOSE ASSIGNMENT")
    if choice is not None:
        if not suppress_print:
            print(" > CHOICE:", choices[choice])
        return assignments[choice]
    else:
        if not suppress_print:
            print(" X CHOICE: NONE")
        return None


def get_assignment(assignment_id: int = None) -> Assignment:
    assn_d = _gh_api(f"assignments/{assignment_id}")
    if not assn_d:
        return None
    try:
        assignment = from_dict(Assignment, assn_d)
    except:
        logger.exception("Error converting Assignment")
        return None
    return assignment


###############################################################################
# get_accepted_assignments
###############################################################################


@overload
def get_accepted_assignments(assignment: int) -> List[AcceptedAssignment]: ...


@overload
def get_accepted_assignments(assignment: Assignment) -> List[AcceptedAssignment]: ...


def get_accepted_assignments(
    accepted_assignment: Assignment,
) -> List[AcceptedAssignment]:
    if isinstance(accepted_assignment, Assignment):
        assignment_id = accepted_assignment.id
    elif isinstance(accepted_assignment, int):
        assignment_id = accepted_assignment
    else:
        raise ValueError("assignment must be either int or Assignment")

    accepted_assignments: List[AcceptedAssignment] = []

    accepted_assignments_d = _gh_api(
        f"assignments/{assignment_id}/accepted_assignments"
    )
    if not accepted_assignments_d:
        return []
    for acc_assn_d in accepted_assignments_d:
        try:
            accepted_assignment = from_dict(AcceptedAssignment, acc_assn_d)
        except:
            logger.exception("Error converting AcceptedAssignment")
            return None
        accepted_assignments.append(accepted_assignment)
    return accepted_assignments


if __name__ == "__main__":
    c = choose_classroom()
    print(c)

    draw_single_line()

    a = choose_assignment(c)

    print(a)

    AcceptedAssignment.get_table_header()

    aa_list = get_accepted_assignments(a)
    for aa in aa_list:
        print(aa)
