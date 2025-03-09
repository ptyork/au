import click
from rich.console import Console

from f_table import get_table, BasicScreenStyle

from au.click import AliasedGroup, AssignmentOptions, RosterOptions, BasePath
from au.classroom import (
    ClassroomSettings,
    Roster,
    get_classroom,
    choose_classroom,
    get_accepted_assignments,
    AcceptedAssignment,
)

from .rename_roster import rename_roster
from .commit_all import commit_all
from .clone_all import clone_all_cmd
from .time_details import time_details


@click.group(cls=AliasedGroup)
def classroom():
    """Commands for working with GitHub Classroom."""


classroom.add_command(rename_roster)
classroom.add_command(commit_all)
classroom.add_command(clone_all_cmd)
classroom.add_command(time_details)


@classroom.command()
@click.argument("assignment_dir", type=BasePath(), default=".")
@AssignmentOptions(required=True, load=False, store=True, force_store=True).options
@RosterOptions(load=False, store=True, prompt=True).options
def configure(assignment_dir, **kwargs):
    """Create or change settings for ASSIGNMENT_DIR.

    Most commands that accept configuration parameters such as an assignment-id
    or roster file will save this to a local configuration file. However, this
    command is useful if you need to change the settings or if you are
    pre-configuring an assignment directory prior to cloning student
    submissions.

    If not specified, ASSIGNMENT_DIR defaults to the current directory.
    """
    settings = ClassroomSettings(assignment_dir)
    if settings:
        print(f"Settings saved in {settings.settings_doc_path / settings.FILENAME}")
    else:
        print(f"Error encountered while configuring {assignment_dir}")


@classroom.command()
@click.option(
    "-c",
    "--classroom-id",
    type=int,
    help="The ID of the classroom to fetch",
    default=None,
)
def open_classroom(classroom_id: int = None):
    """Open a classroom in the default web browser.

    This command is simply a convenience method for those that work primarily
    from the command line.
    """
    if classroom_id:
        room = get_classroom(classroom_id)
    else:
        room = choose_classroom()
    if room:
        click.launch(room.url)


@classroom.command()
@AssignmentOptions(required=True, store=False).options
def info(assignment):
    """Display details for an assignment.

    Details include the due date, assignment type, and a count of accepted and
    submitted assignments, among others.

    If executed inside of a configured assignment directory, it will display the
    information for the configured assignment. If not, it will prompt the user
    to select a classroom and assignment.
    """
    print(assignment.as_table())


@classroom.command()
@AssignmentOptions(required=True, store=False).options
@RosterOptions(required=False, load=False, store=False, prompt=True).options
def accepted(assignment, roster: Roster):
    """List accepted assignments for an  assignment."""
    with Console().status(
        "Retrieving data from GitHub Classroom", spinner="bouncingBall"
    ):
        rows = []
        for assn in get_accepted_assignments(assignment):
            name = None
            if assn.login:
                if roster:
                    name = roster.get_name(assn.login)
                if not name:
                    name = assn.login
            if not name:
                name = "NO NAME"
            rows.append([name, assn.commit_count, assn.repository.html_url])
        rows.sort(key=lambda row: row[0].casefold())
    print(
        get_table(
            header_row=["STUDENT", "COMMITS", "REPOSITORY"],
            value_rows=rows,
            col_defs=["", "^", "A"],
            style=BasicScreenStyle(),
        )
    )


if __name__ == "__main__":
    classroom()
