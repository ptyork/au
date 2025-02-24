import click
from au.lib.click import AliasedGroup

# @click.command(cls=SubdirGroup, file=__file__, module=__package__)
@click.version_option(prog_name='au-utils')
@click.group(cls=AliasedGroup)
def main():
    """
    AU CLASSROOM AUTOMATION TOOLS

    Solid gold tools for automating much of the workflow involved in managing
    and grading assignments using GitHub Classroom.
    """
    pass

from .classroom.cli import classroom
main.add_command(classroom)

from .python.cli import python
main.add_command(python)

from .sql.cli import sql
main.add_command(sql)


# @main.command()
# @click.argument('name', type=str)
# def embed2(name: str):
#     """
#     Command embedded in cli.py.
    
#     Much longer stuff below here.
#     """
#     click.echo("Testing a command embedded directly in cli.py")

if __name__ == "__main__":
    main()
