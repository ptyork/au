from typing import List
import logging
import sys
from pathlib import Path
from pprint import pformat

import click
from rich.console import Console

from f_table import get_table, BasicScreenStyle
from git_wrap import GitRepo, get_git_dirs

from au.classroom import Assignment, Roster, get_accepted_assignments
from au.click import BasePath, AssignmentOptions, RosterOptions, DebugOptions
from au.common import draw_double_line, draw_single_line


logger = logging.getLogger(__name__)


@click.command("clone-all")
@click.argument("root_dir", type=BasePath(), default=".")
@AssignmentOptions(required=True).options
@RosterOptions(prompt=True).options
@click.option(
    "--preserve-prefix",
    is_flag=True,
    help="set to preserve the prefix (slug) string common to all repositories",
)
@click.option(
    "-u",
    "--update",
    is_flag=True,
    help="set to pull changes to existing repositories",
)
@click.option(
    "-y",
    "--skip-confirm",
    is_flag=True,
    help="set to bypass confirmation and overwrite existing CSV",
)
@click.option(
    "-p",
    "--preview",
    is_flag=True,
    help="set to show changes without actually making them",
)
@DebugOptions().options
def clone_all_cmd(
    root_dir: Path,
    assignment: Assignment = None,
    roster: Roster = None,
    preserve_prefix: bool = False,
    update: bool = False,
    skip_confirm: bool = False,
    preview: bool = False,
    **kwargs,
):
    """Clone all student repos for an assignment into ROOT_DIR.

    This command will use the specified assignment to query GitHub Classroom for
    all accepted assignments. For each, it will run the following logic:

    \b
        if repository directory exists in ROOT_DIR
            if update flag is set
                pull updates from GitHub
            else
                skip
        else
            if repository has submissions
                clone repository into ROOT_DIR
            else
                skip

    If no roster is provided, directory names will match the students' GitHub
    login names. If a GitHub Classroom roster is provided using the --roster
    option and a student name match can be found in the roster, then the
    directory will be named as follows:

        [student_name]@[login_name]

    All commas, spaces, and invalid characters in the student name will be
    replaced with underscores. for example:

        York_Paul@ptyork

    If the `--preserve-prefix` flag is set, then the prefix (also called 'slug')
    will be added to all assignments, as they are in GitHub. This will insure
    that all student assignment directory names are unique.

    If ROOT_DIR is not provided, then the current working directory will be
    assumed.
    """
    logging.basicConfig()

    draw_double_line()
    print(assignment)
    draw_single_line()
    if roster:
        print(f"USING ROSTER: {roster.file.resolve()}")
    else:
        print("NOT USING ROSTER")
    draw_single_line()

    if not skip_confirm:
        if not click.confirm(
            f"Are you sure you want to clone the above assignment into {root_dir}?"
        ):
            sys.exit(0)

    clone_all(root_dir, assignment, roster, preserve_prefix, update, preview)


def clone_all(
    root_dir: Path,
    assignment: Assignment,
    roster: Roster = None,
    preserve_prefix: bool = False,
    update: bool = False,
    preview: bool = False,
):
    """clone all student submissions for an assignment into root_dir."""
    if preview:
        print()
        draw_double_line()
        draw_single_line("PREVIEW ONLY - NO CHANGES BEING MADE")
        draw_double_line()
        print()

    if assignment.type not in ["individual", "group"]:
        logger.fatal("Only 'individual' and 'group' assignments are supported")
        sys.exit(1)

    assignment_prefix = assignment.slug + "-"

    if roster and assignment.type != "individual":
        logger.warning(
            "Use of GitHub classroom roster only valid for individual assignments."
        )
        roster = None

    console = Console()
    with console.status(
        "Retrieving data from GitHub Classroom", spinner="bouncingBall"
    ) as status:
        accepted_assignments = get_accepted_assignments(assignment)

        submitted_assignments = [a for a in accepted_assignments if a.commit_count > 0]
        unsubmitted_assignments = [
            a for a in accepted_assignments if a.commit_count == 0
        ]

        if assignment.type == "individual":
            # Get the student name for individual assignments
            accepted_logins = [a.students[0].login for a in accepted_assignments]
            submitted_logins = [a.students[0].login for a in submitted_assignments]
            unsubmitted_logins = [a.students[0].login for a in unsubmitted_assignments]
            login_url_map = {
                a.students[0].login: a.repository.html_url
                for a in submitted_assignments
            }
        else:
            # Get the group name for group assignments
            accepted_logins = [
                a.repository.name.removeprefix(assignment_prefix)
                for a in accepted_assignments
            ]
            submitted_logins = [
                a.repository.name.removeprefix(assignment_prefix)
                for a in submitted_assignments
            ]
            unsubmitted_logins = [
                a.repository.name.removeprefix(assignment_prefix)
                for a in unsubmitted_assignments
            ]
            login_url_map = {
                a.repository.name.removeprefix(assignment_prefix): a.repository.html_url
                for a in submitted_assignments
            }
        if not roster:
            roster = Roster(accepted_logins)
        else:
            # Add all...will ignore ones already in the roster
            for login in accepted_logins:
                roster.append(login)

        status.update(status="Checking status of existing repositories")

        existing_repo_dirs = get_git_dirs(root_dir)

        login_all_dir_map = roster.get_login_dir_map(root_dir)
        login_pull_dir_map = roster.get_login_dir_map(existing_repo_dirs)
        login_bad_dir_map = {
            login: path
            for login, path in login_all_dir_map.items()
            if login not in login_pull_dir_map
        }

        login_clone_dir_map = roster.get_dir_names(
            assignment_prefix if preserve_prefix else None
        )
        for login in roster.get_logins():
            if login not in submitted_logins:
                login_clone_dir_map.pop(login, None)
        for login in login_pull_dir_map:
            login_clone_dir_map.pop(login, None)
        for login in login_bad_dir_map:
            login_clone_dir_map.pop(login, None)

        clones: List[str] = []
        pulls: List[str] = []
        skips: List[str] = []
        errors: List[str] = []

        logger.debug("login_clone_dir_map: " + pformat(login_clone_dir_map))
        logger.debug("login_pull_dir_map" + pformat(login_all_dir_map))
        logger.debug("login_bad_dir_map" + pformat(login_bad_dir_map))

        for login, dir_name in login_clone_dir_map.items():
            repo_url = login_url_map[login]
            status.update(status=f"CLONING {dir_name} from {repo_url}")
            if not preview:
                repo_path = root_dir / dir_name
                try:
                    GitRepo.clone(repo_url, repo_path)
                except:
                    logger.exception(
                        f"Exception raised while cloning from {repo_url} into {repo_path}"
                    )
                    errors.append(roster.get_name(login))

        if update:
            for login, dir_name in login_pull_dir_map.items():
                try:
                    repo = GitRepo(root_dir / dir_name)
                    if preview:
                        status.update(status=f"Checking remote status for {dir_name}")
                        if repo.needs_pull():
                            pulls.append(roster.get_name(login))
                        else:
                            skips.append(roster.get_name(login))
                    else:
                        status.update(status=f"PULLING {dir_name}")
                        if repo.pull():
                            pulls.append(roster.get_name(login))
                        else:
                            skips.append(roster.get_name(login))
                except:
                    logger.exception(f"Exception raised while pulling {dir_name}")
                    errors.append(roster.get_name(login))
        else:
            pulls = [roster.get_name(l) for l in login_pull_dir_map]

    unsubmitted = [roster.get_name(login) for login in unsubmitted_logins]
    unaccepted = [
        roster.get_name(login)
        for login in roster.get_logins()
        if login not in accepted_logins
    ]

    summary_rows = []
    if clones:
        clones.sort()
        summary_rows.append([f"Cloned ({len(clones)})", "\n".join(clones)])
    else:
        summary_rows.append(
            ["Pulled (0)", "No uncloned repositories for this assignment"]
        )
    if pulls:
        pulls.sort()
        pull_str = "Pulled" if update else "Not Pulled: no --update"
        summary_rows.append([f"{pull_str} ({len(pulls)})", "\n".join(pulls)])
    if skips:
        skips.sort()
        summary_rows.append(
            [f"Not Pulled - No Changes ({len(skips)})", "\n".join(skips)]
        )
    if unsubmitted:
        unsubmitted.sort()
        summary_rows.append(
            [f"Not Submitted ({len(unsubmitted)})", "\n".join(unsubmitted)]
        )
    if unaccepted:
        unaccepted.sort()
        summary_rows.append(
            [f"Not Accepted ({len(unaccepted)})", "\n".join(unaccepted)]
        )
    if errors:
        errors.sort()
        summary_rows.append([f"Errors ({len(errors)})", "\n".join(errors)])

    print(get_table(summary_rows, style=BasicScreenStyle(), separete_rows=True))


if __name__ == "__main__":
    clone_all_cmd()
