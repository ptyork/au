import click
from au.click import AliasedGroup
from importlib.metadata import version, PackageNotFoundError

from .assignment import assignment
from .python import python
from .repo import repo
from .sql import sql


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
    au - GitHub Classroom Automation Tools

    The gold standard for managing GitHub Classroom assignments at scale. These
    tools help to automate the workflows required to create, administer,
    evaluate, and provide feedback for assignments.

    Homepage: https://ptyork.github.io/au
    """


main.add_command(assignment)
main.add_command(python)
main.add_command(repo)
main.add_command(sql)


if __name__ == "__main__":
    main()
