import click
from yaspin import yaspin

from au.lib.click.AliasedGroup import AliasedGroup
from au.lib.github.classroom_util import get_classroom, choose_classroom, get_assignment, choose_assignment, get_accepted_assignments
from au.lib.github.classroom_types import AcceptedAssignment


@click.group("classroom", short_help="Commands for working with GitHub Classroom.", cls=AliasedGroup)
def main():
    pass

from .rename_roster import rename_roster
main.add_command(rename_roster)

from .commit_all import commit_all
main.add_command(commit_all)

@main.command()
@click.option('-c', '--classroom-id', type=int, help="The ID of the classroom to fetch", default=None)
def classroom_info(classroom_id: int = None):
    '''
    Display details for a specified classroom
    '''
    if classroom_id:
        room = get_classroom(classroom_id)
    else:
        room = choose_classroom()
        if room:
            # get more details
            room = get_classroom(room.id)
    if room:
        print(room.as_table())

@main.command()
@click.option('-c', '--classroom-id', type=int, help="The ID of the classroom to fetch", default=None)
def open_classroom(classroom_id: int = None):
    '''
    Open a classroom in the default web browser
    '''
    if classroom_id:
        room = get_classroom(classroom_id)
    else:
        room = choose_classroom()
    if room:
        click.launch(room.url)

@main.command()
@click.option('-a', '--assignment-id', type=int, help="The ID of the assignment to fetch", default=None)
@click.option('-c', '--classroom-id', type=int, help="If specified, filter assignments by this classroom ID", default=None)
def assignment_info(classroom_id=None, assignment_id=None):
    '''
    Display details for a specified assignment
    '''
    if assignment_id:
        a = get_assignment(assignment_id)
    elif classroom_id:
        a = choose_assignment(classroom_id)
    else:
        c = choose_classroom()
        a = choose_assignment(c)
    print(a.as_table())


@main.command()
@click.option('-a', '--assignment-id', type=int, help="The ID of the assignment", default=None)
@click.option('-c', '--classroom-id', type=int, help="If specified, filter assignments by this classroom ID", default=None)
def show_accepted(classroom_id=None, assignment_id=None):
    '''
    List accepted assignments for a selected assginemnt
    '''
    if (assignment_id):
        a = get_assignment(assignment_id)
    else:
        c = choose_classroom(classroom_id)
        a = choose_assignment(c)
    print(a)
    print(AcceptedAssignment.get_table_header())
    with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic as sp:
        aa_list = get_accepted_assignments(a)
    for aa in aa_list:
        print(aa.as_table_row())

