import click
from yaspin import yaspin

from au.lib.click.AliasedGroup import AliasedGroup
from au.lib.github.classroom_util import get_course, get_assignment, choose_assignment, get_accepted_assignments
from au.lib.github.classroom_types import AcceptedAssignment


@click.group("classroom", short_help="Commands for working with GitHub Classroom.", cls=AliasedGroup)
def main():
    pass

from .rename_roster import rename_roster
main.add_command(rename_roster)

from .commit_all import commit_all
main.add_command(commit_all)

@main.command()
@click.option('-c', '--course-id', type=int, help="The ID of the course to fetch", default=None)
def course_info(course_id: int):
    '''
    Display details for a specified course
    '''
    print(get_course(course_id))

@main.command()
@click.option('-a', '--assignment-id', type=int, help="The ID of the assignment to fetch", default=None)
@click.option('-c', '--course-id', type=int, help="If specified, filter assignments by this course ID", default=None)
def assignment_info(course_id=None, assignment_id=None):
    '''
    Display details for a specified assignment
    '''
    if (assignment_id):
        with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic as sp:
            c, a = get_assignment(assignment_id)
    else:
        c = get_course(course_id)
        a = choose_assignment(c)
    print('COURSE:')
    print(c)
    print('ASSIGNMENT:')
    print(a)


@main.command()
@click.option('-a', '--assignment-id', type=int, help="The ID of the assignment", default=None)
@click.option('-c', '--course-id', type=int, help="If specified, filter assignments by this course ID", default=None)
def show_accepted(course_id=None, assignment_id=None):
    '''
    List accepted assignments for a selected assginemnt
    '''
    if (assignment_id):
        c, a = get_assignment(assignment_id)
    else:
        c = get_course(course_id)
        a = choose_assignment(c)
    print('COURSE:')
    print(c)
    print('ASSIGNMENT:')
    print(a)
    AcceptedAssignment.print_header()
    with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic as sp:
        aa_list = get_accepted_assignments(a)
    for aa in aa_list:
        print(aa)

