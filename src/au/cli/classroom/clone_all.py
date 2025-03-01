from typing import List
import logging
import sys
from pathlib import Path
from pprint import pformat

import click
from rich.console import Console

from f_table import get_table, BasicScreenStyle
from simple_git import GitRepo, get_git_dirs

from au.click import BasePath, AssignmentOptions, RosterOptions, DebugOptions
from au.tools import draw_double_line, draw_single_line
from au.classroom import Assignment, Roster, get_accepted_assignments


logger = logging.getLogger(__name__)


@click.command('clone-all')
@click.argument("root_dir",type=BasePath(), default='.')
@AssignmentOptions().options
@RosterOptions().options
@click.option("-pp","--preserve-prefix", is_flag=True, help="set to preserve the prefix (slug) string common to all repositories")
@click.option("-u", "--update", is_flag=True, help="set to pull changes to existing repositories")
@click.option("--preview", is_flag=True, help="set to show changes without actually making them")
@DebugOptions().options
def clone_all_cmd(root_dir: Path,
                  assignment: Assignment = None,
                  roster: Roster = None,
                  preserve_prefix: bool = False,
                  update: bool = False,
                  preview: bool = False,
                  **kwargs):
    '''Clone all student repositories for an assignment into ROOT_DIR.

    \b Required Argument:
      ROOT_DIR
        the base directory into which assignmetns will be cloned.

    This command will use the specified|selected assignment to query GitHub
    Classroom for all accepted assignments. For each, it will run the following
    logic:

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

    By default, repositories will be named as they are in GitHub. However, to
    assist with sorting and identification, two additional options are provided.

    If a GitHub Classroom roster is provided using the --roster option and a
    student name match can be found in the roster, then the directory will be
    named as follows:

        [prefix][student_name]@[login_name]

    All commas, spaces, and invalid characters in the student name will be
    replaced with underscores. for example:
    
        hw1-York_Paul@ptyork
    
    If the --remove-prefix then the prefix (also called 'slug') will be removed
    from all assignments, whether or not a roster has been provided. So
    directory names will either be named:

        [login_name]
    
    or:
    
        [student_name]@[login_name]
    '''
    logging.basicConfig()

    if not assignment:
        logger.fatal("Unable to find the requested assignment.")
        sys.exit(1)
    
    draw_double_line()
    print(assignment)
    draw_single_line()
    if roster:
        print(f"USING ROSTER: {roster.file.resolve()}")
    else:
        print("NOT USING ROSTER")
    draw_single_line()

    clone_all(root_dir, assignment, roster, preserve_prefix, update, preview)


def clone_all(root_dir: Path,
              assignment: Assignment,
              roster: Roster = None,
              preserve_prefix: bool = False,
              update: bool = False,
              preview: bool = False):
    """clone all student submissions for an assignment into root_dir."""

    if assignment.type not in ['individual','group']:
        logger.fatal("Only 'individual' and 'group' assignments are supported")
        sys.exit(1)

    assignment_prefix = assignment.slug + '-'

    if roster and assignment.type != 'individual':
        logger.warning("Use of GitHub classroom roster only valid for individual assignments.")
        roster = None
    
    console = Console()
    with console.status("Retrieving data from GitHub Classroom", spinner="bouncingBall") as status:
        accepted_assignments = get_accepted_assignments(assignment)

        submitted_assignments = [a for a in accepted_assignments if a.commit_count > 0]
        unsubmitted_assignments = [a for a in accepted_assignments if a.commit_count == 0]

        if assignment.type == 'individual':
            # Get the student name for individual assignments
            accepted_logins = [a.students[0].login for a in accepted_assignments]
            submitted_logins = [a.students[0].login for a in submitted_assignments]
            unsubmitted_logins = [a.students[0].login for a in unsubmitted_assignments]
            login_url_map = {a.students[0].login:a.repository.html_url for a in submitted_assignments}
        else:
            # Get the group name for group assignments
            accepted_logins = [a.repository.name.removeprefix(assignment_prefix) for a in accepted_assignments]
            submitted_logins = [a.repository.name.removeprefix(assignment_prefix) for a in submitted_assignments]
            unsubmitted_logins = [a.repository.name.removeprefix(assignment_prefix) for a in unsubmitted_assignments]
            login_url_map = {a.repository.name.removeprefix(assignment_prefix):a.repository.html_url for a in submitted_assignments}
        if not roster:
            roster = Roster(accepted_logins)
        else:
            # Add all...will ignore ones already in the roster
            for login in accepted_logins:
                roster.append(login)

        status.update(status="Checking for existing repositories")

        existing_repo_dirs = get_git_dirs(root_dir)

        login_all_dir_map = roster.get_login_dir_map(root_dir)
        login_pull_dir_map = roster.get_login_dir_map(existing_repo_dirs)
        login_bad_dir_map = {login:path for login, path in login_all_dir_map.items() if login not in login_pull_dir_map}

        login_clone_dir_map = roster.get_dir_names(assignment_prefix if preserve_prefix else None)
        for login in roster.get_logins():
            if login not in submitted_logins:
                login_clone_dir_map.pop(login, None)
        for login in login_pull_dir_map:
            login_clone_dir_map.pop(login, None)
        for login in login_bad_dir_map:
            login_clone_dir_map.pop(login, None)

        errors: List[str] = []

        logger.debug("login_clone_dir_map: " + pformat(login_clone_dir_map))
        logger.debug("login_pull_dir_map" + pformat(login_all_dir_map))
        logger.debug("login_bad_dir_map" + pformat(login_bad_dir_map))

        for login, dir_name in login_clone_dir_map.items():
            repo_url = login_url_map[login]
            if preview:
                print(f"WOULD CLONE {dir_name} from {repo_url}")
            else:
                repo_path = root_dir / dir_name
                try:
                    status.update(status=f"CLONING {dir_name} from {repo_url}")
                    GitRepo.clone(repo_url, repo_path)
                except:
                    logger.exception(f"Exception raised while cloning from {repo_url} into {repo_path}")
                    errors.append(dir_name)

        if update:
            for login, dir_name in login_pull_dir_map.items():
                if preview:
                    print(f"WOULD PULL {dir_name}")
                else:
                    repo_path = root_dir / dir_name
                    try:
                        status.update(status=f"PULLING from {dir_name}")
                        GitRepo(repo_path).pull()
                    except:
                        logger.exception(f"Exception raised while pulling {repo_path}")
                        errors.append(dir_name)

    clones = [v for v in login_clone_dir_map.values() if v not in errors]
    pulls = [v for v in login_pull_dir_map.values() if v not in errors]
    unsubmitted = [roster.get_name(login) for login in unsubmitted_logins]
    unaccepted = [roster.get_name(login) for login in roster.get_logins() if login not in accepted_logins]

    summary_rows = []
    if clones:
        summary_rows.append([f'Cloned ({len(clones)})', '\n'.join(clones)])
    if pulls:
        pull_str = 'Pulled' if update else 'Not Pulled'
        summary_rows.append([f'{pull_str} ({len(pulls)})', '\n'.join(pulls)])
    if unsubmitted:
        summary_rows.append([f'Not Submitted ({len(unsubmitted)})', '\n'.join(unsubmitted)])
    if unaccepted:
        summary_rows.append([f'Not Accepted ({len(unaccepted)})', '\n'.join(unaccepted)])
    if errors:
        summary_rows.append([f'Errors ({len(errors)})', '\n'.join(errors)])

    print(get_table(summary_rows, style=BasicScreenStyle()))

if __name__ == '__main__':
    clone_all_cmd()
