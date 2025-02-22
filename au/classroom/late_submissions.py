#!/usr/bin/env python3

from datetime import datetime, timezone
from typing import Dict

import click
from yaspin import yaspin

import sys
from io import TextIOWrapper
from pathlib import Path
from git import Repo
from pprint import pformat

from au.lib.common.csv import dict_from_csv
from au.lib.common.datetime import get_friendly_local_datetime, get_friendly_timedelta
from au.lib.common.label_dir import label_dir, FileType
from au.lib.common.terminal import draw_double_line
from au.lib.f_table import get_table, BasicScreenStyle
from au.lib.classroom import Assignment, Classroom
from au.lib.classroom import choose_assignment, choose_classroom, get_accepted_assignments, get_assignment

import logging
logger = logging.getLogger(__name__)

@click.command('late-submissions')
@click.argument("root_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("-a", "--assignment-id", type=int,
              help="the integer classroom id for the assignment; will prompt for the classroom and assignment if not provided")
@click.option("-r", "--roster", type=click.File(),
              help="A GitHub Classroom roster file (usually named `classroom_roster.csv`. If provided, directories will be named using the associated student name as well as the student's GitHub login name.")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
def late_submissions(root_dir: Path,
                     assignment_id: int = None,
                     roster: TextIOWrapper = None,
                     remove_prefix: bool = False,
                     debug: bool = False,
                     quiet: bool = False):
    '''Show all late submissions for assignments in ROOT_DIR.'''
    logging.basicConfig()

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # process roster to get mapping of logins to students
    login_student_map = None
    if roster:
        try:
            login_student_map = dict_from_csv(roster, 'github_username', 'identifier')
            logger.debug(pformat(login_student_map))
        except Exception as ex:
            logger.error(f"Error encountered while processing roster: {ex}")
            sys.exit(1)


    if assignment_id:
        assignment = get_assignment(assignment_id)
    else:
        classroom: Classroom = choose_classroom()
        assignment: Assignment = choose_assignment(classroom)

    if not assignment:
        logger.fatal("Unable to find the requested assignment.")
        sys.exit(1)
    
    draw_double_line()
    print(assignment)

    # Pull logins to map to the roster, but only if the roster is provided and
    # this is an individual assignment
    accepted_logins = None
    if login_student_map and assignment.type == 'individual':
        # Attempt to get logins for all students to match against the dirs
        with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic:
            accepted = get_accepted_assignments(assignment)
            accepted_logins = [a.students[0].login for a in accepted]
        logger.debug("accepted_logins: " + pformat(accepted_logins))

    # Use the label_dir function to map logins to directories
    dir_login_map = None
    if accepted_logins:
        login_login = {login:login for login in accepted_logins}
        dir_login_map = label_dir(login_login, root_dir, FileType.DIRECTORY)
        logger.debug("dir_login_map: " + pformat(dir_login_map))

    repo_dirs: Dict[str, Repo] = {}
    with yaspin(text="Finding all repositories. Please wait...").aesthetic:
        for sub_dir in root_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            try:
                repo_dirs[sub_dir.name] = Repo(sub_dir)
            except:
                continue
    logger.debug("repo_dirs: " + pformat(repo_dirs.keys()))

    self_email = None
    students_past_due = {}
    with yaspin(text="Finding late submissions. Please wait...").aesthetic:
        for student, repo in repo_dirs.items():
            if not self_email:
                self_email = repo.config_reader("global").get_value('user', 'email')
                logger.debug("self_email: " + str(self_email))

            if dir_login_map:
                login = dir_login_map.get(student)
                student = login_student_map.get(login)
            else:
                student = student

            commits = []
            for commit in repo.iter_commits():
                if commit.author.email == self_email:
                    continue
                if "[bot]" in commit.author.name:
                    break
                commit_date = datetime.fromtimestamp(commit.committed_date, timezone.utc)
                if commit_date <= assignment.deadline and not commits:
                    break   # on time
                else:
                    commits.append([commit_date, commit.message.strip()])

            if commits:
                students_past_due[student] = commits

    logger.debug("students_past_due: " + pformat(students_past_due))
    sorted_past_due = list(students_past_due.keys())
    sorted_past_due.sort()

    # FINALLY print the results
    past_due_rows = []
    for student in sorted_past_due:
        commits = students_past_due.get(student)
        commit_date, message = commits.pop(0)
        past_due = get_friendly_timedelta(commit_date - assignment.deadline)
        friendly_date = get_friendly_local_datetime(commit_date)
        past_due_rows.append([student,past_due,friendly_date,message])
        for commit_date, message in commits:
            friendly_date = get_friendly_local_datetime(commit_date)
            past_due_rows.append(['','',friendly_date,message])
    print(get_table(past_due_rows,
                    header_row=['STUDENT','AMOUNT','COMMIT DATE','COMMIT MESSAGE'],
                    col_defs=['','','','A'],
                    style=BasicScreenStyle()))

if __name__ == '__main__':
    late_submissions()
