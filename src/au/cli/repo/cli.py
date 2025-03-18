import click

from au.click import AliasedGroup

from .create import create


@click.command(cls=AliasedGroup)
def repo():
    """Commands for working with GitHub Repositories."""
    pass


repo.add_command(create)


# TODO: Add gh api /gitignore/templates call to list templates

# TODO: Add simple to_columns function to terminal.py to handle large list

# TODO: Add copy_from() to create a new assignment repository as a copy of another

# TODO: Add copy_to() to create a new assignment repository as a copy of another

# TODO: Add functions to make it easy to synchronize multiple identical repos,
#       as is always the case with GitHub classroom templates.

if __name__ == "__main__":
    repo()
