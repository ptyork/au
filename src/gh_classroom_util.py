#!/usr/bin/env python3

from typing import Tuple

import subprocess

import re

from gh_classroom_types import Course, Assignment
from datetime_util import parse_github_datetime, get_friendly_local_datetime
from terminal_util import clean_ansi, draw_single_line, get_choice

###############################################################################
# get_course
###############################################################################

def get_course(course_id = None) -> Course:
    cmd = 'gh classroom list'
    result = subprocess.run(cmd.split(), capture_output=True, text=True)

    lines = result.stdout.splitlines()

    header_line = lines.pop(0).lower()
    while lines and not header_line.startswith('id'):
        header_line = lines.pop(0).lower()

    # This output is space-separated, so we need to use regular expressions to determine
    # the start and end of each column.

    id_match = re.search(r'id\s+', header_line)
    name_match = re.search(r'name\s+', header_line)

    if not id_match and name_match:
        print("Unable to parse gh classroom results")
        exit(1)

    courses: list[Course] = []

    for line in lines:
        id = int(line[id_match.start():id_match.end()])
        name = line[name_match.start():name_match.end()].strip()
        courses.append(Course(id, name))

    if course_id:
        for course in courses:
            if course.id == course_id:
                return course
        return None
    else:
        courses.reverse()
        choices = [course.name for course in courses]
        choice = get_choice(choices, "AVAILABLE COURSES", "Choose Course")
        return courses[choice]

###############################################################################
# choose_assignment
###############################################################################

def choose_assignment(course: Course) -> Assignment:
    cmd = f'gh classroom assignments -c {course.id}'
    result = subprocess.run(cmd.split(), capture_output=True, text=True)

    lines = result.stdout.splitlines()

    header_line = lines.pop(0).lower()
    while lines and not header_line.startswith('id'):
        header_line = lines.pop(0).lower()

    # But for some reason these are tab separated, so we split on tabs and find
    # the right index, instead

    col_names = header_line.split("\t")

    try:
        id_idx = col_names.index('id')
        title_idx = col_names.index('title')
        deadline_idx = col_names.index('deadline')
    except:
        print("Unable to parse gh classroom results")
        exit(1)

    assignments = []

    for line in lines:
        cols = line.split("\t")
        id = int(cols[id_idx])
        title = cols[title_idx].strip()
        deadline_str = cols[deadline_idx].strip()
        deadline = parse_github_datetime(deadline_str)
        assignments.append(Assignment(id, title, deadline))

    assignments.sort(key=lambda a: a.title)
    choices = [assignment.title for assignment in assignments]
    choice = get_choice(choices, "AVAILABLE ASSIGNMENTS", "Choose Assignment")
    return assignments[choice]


###############################################################################
# get_assignment
###############################################################################

def get_assignment(assignment_id: int = None) -> Tuple[Course, Assignment]:
    cmd = f'gh classroom assignment -a {assignment_id}'
    result = subprocess.run(cmd.split(), capture_output=True, text=True)

    text = result.stdout
    text = clean_ansi(text)

    lines = text.splitlines()

    if len(lines) < 5:
        return None

    course_id = None
    course_name = None
    assignment_title = None
    assignment_deadline = None

    for line in lines:
        parts = line.split(': ')
        if len(parts) < 2:
            continue

        name = parts[0].lower()
        value = ''.join(parts[1:])

        
        match name:
            case 'id':
                # The first ID will be the course ID, so skip it has already been encountered
                course_id = int(value)
            case 'name':
                course_name = value
            case 'title':
                assignment_title = value
            case 'deadline':
                assignment_deadline = parse_github_datetime(value)

    c = Course(course_id, course_name)
    a = Assignment(assignment_id, assignment_title, assignment_deadline)

    return c, a


def print_course(course: Course) -> None:
    print(f"Course Name :       {course.name}")
    print(f"Course ID :         {course.id}")


def print_assignment(assignment: Assignment) -> None:
    print(f"Assignment Title :  {assignment.title}")
    print(f"Assignment ID :     {assignment.id}")
    print(f"Deadline :          {get_friendly_local_datetime(assignment.deadline)}")


if __name__ == "__main__":
    c = get_course()
    a = get_assignment(c)

    print_course(c)
    print_assignment(a)

    # draw_single_line()

    # print(c.as_json())
    # draw_single_line()

    # c2 = get_course(c.id)
    # print(c2.as_json())

    # a = choose_assignment(c)
    # draw_single_line()

    # js = a.as_json();
    # print(js)
    # draw_single_line()

    # a2 = Assignment.from_json(js)
    # js2 = a2.as_json();
    # print(js2)
    # draw_single_line()

    # a3 = get_assignment(a.id)
    # js3 = a3.as_json();
    # print(js3)
