import click
from yaspin import yaspin

from au.lib.click import AliasedGroup, AssignmentOptions, RosterOptions, BasePath
from au.lib.classroom import get_classroom, choose_classroom, get_assignment, choose_assignment, get_accepted_assignments
from au.lib.classroom import AcceptedAssignment
from au.lib.f_table.f_table import get_table, BasicScreenStyle


@click.group(cls=AliasedGroup)
def classroom():
    """Commands for working with GitHub Classroom."""
    pass


from .rename_roster import rename_roster
classroom.add_command(rename_roster)

from .commit_all import commit_all
classroom.add_command(commit_all)

from .clone_submissions import clone_submissions_cmd
classroom.add_command(clone_submissions_cmd)

from .late_submissions import late_submissions
classroom.add_command(late_submissions)

@classroom.command()
@click.argument("assignment_dir",type=BasePath(), default='.')
@AssignmentOptions(load=False, store=True).options
@RosterOptions(load=False, store=True, prompt=True).options
def configure_assignment_dir(**kwargs):
    '''Create or change settings for ASSIGNMENT_DIR (defaults to current working directory)'''
    ...


@click.option('-c', '--classroom-id', type=int, help="The ID of the classroom to fetch", default=None)
def open_classroom(classroom_id: int = None):
    '''Open a classroom in the default web browser'''
    if classroom_id:
        room = get_classroom(classroom_id)
    else:
        room = choose_classroom()
    if room:
        click.launch(room.url)

@classroom.command()
@AssignmentOptions(store=False).options
def assignment_info(assignment):
    '''Display details for a specified assignment.'''
    print(assignment.as_table())


@classroom.command()
@AssignmentOptions(store=False).options
def show_accepted(assignment):
    '''List accepted assignments for a selected assginemnt.'''
    print(assignment)
    with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic:
        assignments = get_accepted_assignments(assignment)
        rows = [aa.get_row_cols() for aa in assignments]
    print(get_table(
        header_row=AcceptedAssignment.get_headers(),
        value_rows=rows,
        col_defs=['10','^5','','A'],
        style=BasicScreenStyle()
    ))

if __name__ == "__main__":
    classroom()

