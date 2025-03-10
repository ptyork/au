from typing import Dict, List
from dataclasses import dataclass, field
import logging
import sys
from pathlib import Path
from pprint import pformat

import click
from rich.console import Console

from f_table import get_table, BasicScreenStyle
from git_wrap import GitRepo

from au.classroom import Assignment, get_accepted_assignments, Roster
from au.click import BasePath, AssignmentOptions, RosterOptions, DebugOptions
from au.common import draw_double_line
from au.common.datetime import get_friendly_local_datetime, get_friendly_timedelta


logger = logging.getLogger(__name__)


@click.command()
@click.argument("root_dir", type=BasePath(), default=".")
@AssignmentOptions().options
@RosterOptions(prompt=True).options
@click.option("--late-only", is_flag=True, help="set to only show late students")
@DebugOptions().options
def time_details(
    root_dir: Path,
    assignment: Assignment = None,
    roster: Roster = None,
    late_only: bool = False,
    **kwargs,
):
    """Show submission times for the assignment in ROOT_DIR.

    Details include how long the assignment took to complete and how late (if at
    all) an assignment was.

    If ROOT_DIR is not provided, then the current working directory will be
    assumed.
    """
    logging.basicConfig()

    if not assignment:
        logger.fatal("Unable to find the requested assignment.")
        sys.exit(1)

    draw_double_line()
    print(assignment)

    console = Console()
    with console.status(
        status="Retrieving data from GitHub Classroom", spinner="bouncingBall"
    ) as status:
        # Pull logins to map to the roster, but only if the roster is provided and
        # this is an individual assignment
        accepted_logins = None
        dir_login_map = None
        if roster and assignment.type == "individual":
            # Attempt to get logins for all students to match against the dirs
            accepted = get_accepted_assignments(assignment)
            accepted_logins = [a.students[0].login for a in accepted]
            logger.debug("accepted_logins: " + pformat(accepted_logins))

            dir_login_map = roster.get_dir_login_map(root_dir)

        status.update(status="Finding all local Git repositories")

        repo_dirs: Dict[str, GitRepo] = {}
        for sub_dir in root_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            if sub_dir.name.startswith(("_", ".")):
                continue
            try:
                repo_dirs[sub_dir.name] = GitRepo(sub_dir)
            except:
                continue

        logger.debug("repo_dirs: " + pformat(repo_dirs.keys()))

        @dataclass
        class _Commit:
            date: str
            message: str
            late: bool

        @dataclass
        class _Submission:
            name: str
            date: str = ""
            work_time: str = ""
            past_due: str = ""
            commits: List[_Commit] = field(default_factory=list)

            def add_commit(self, date, message, late):
                self.commits.append(_Commit(date, message, late))

        submissions: List[_Submission] = []
        self_email = GitRepo.get_user_email()

        status.update(status="Gathering time details from each repository")

        for dir_name, repo in repo_dirs.items():
            submission = _Submission(dir_name)
            submissions.append(submission)
            if dir_login_map:
                login = dir_login_map.get(dir_name)
                if login:
                    submission.name = roster.get_name(login)

            last_student_commit_date = None  # assume user submission
            for commit in repo.get_commits():
                if commit.author_email == self_email:
                    continue
                if "GitHub" == commit.committer_name:
                    if last_student_commit_date:
                        submission.work_time = get_friendly_timedelta(
                            last_student_commit_date - commit.date
                        )
                    break
                # assume a student commit
                date_str = get_friendly_local_datetime(commit.date)
                message = commit.message.strip()
                late = commit.date > assignment.deadline
                submission.add_commit(date_str, message, late)
                if not last_student_commit_date:
                    last_student_commit_date = commit.date
                    submission.date = date_str
                    if late:
                        submission.past_due = get_friendly_timedelta(
                            last_student_commit_date - assignment.deadline
                        )

    submissions.sort(key=lambda s: s.name)

    # FINALLY print the results
    rows = []
    for submission in submissions:
        if late_only and (not submission.past_due and submission.commits):
            continue
        past_due = "• • • • • • •"
        time_to_complete = "• • • • • • •"
        date_str = "• • • • • • • • • •"
        message = "• • • • • • • • • •"
        if submission.commits:
            past_due = submission.past_due
            time_to_complete = submission.work_time
            date_str = submission.commits[0].date
            message = submission.commits[0].message
        rows.append([submission.name, past_due, time_to_complete, date_str, message])
        # if late, also show the prior 4 commits
        if submission.past_due:
            for commit in submission.commits[1:5]:
                rows.append(["", "", "", commit.date, commit.message])

    print(
        get_table(
            rows,
            header_row=[
                "NAME",
                "PAST DUE",
                "WORK TIME",
                "COMMIT DATE",
                "COMMIT MESSAGE",
            ],
            col_defs=["", "", "", "", "AT"],
            style=BasicScreenStyle(),
        )
    )


if __name__ == "__main__":
    time_details()
