import click
from au.click import AliasedGroup
from importlib.metadata import version, PackageNotFoundError

from .classroom.cli import classroom
from .python.cli import python
from .sql.cli import sql


MODULE_NAME = "au-tools"
try:
    VERSION = version(MODULE_NAME)
except PackageNotFoundError:
    VERSION = "undetermined"


# @click.command(cls=SubdirGroup, file=__file__, module=__package__)
@click.version_option(VERSION)
@click.group(cls=AliasedGroup)
def main():
    """
    AU CLASSROOM AUTOMATION TOOLS

    Solid gold tools for automating much of the workflow involved in managing
    and grading assignments using GitHub Classroom.
    """


main.add_command(classroom)
main.add_command(python)
main.add_command(sql)


if __name__ == "__main__":
    main()
