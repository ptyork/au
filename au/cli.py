import click
from au.lib.click.SubdirGroup import SubdirGroup

@click.version_option(prog_name='au-utils')
@click.command(cls=SubdirGroup, file=__file__, module=__package__)
def main():
    """
    AU CLASSROOM AUTOMATION TOOLS

    Solid gold tools for automating much of the workflow involved in managing
    and grading assignments using GitHub Classroom.
    """
    pass

# @main.command()
# @click.argument('name', type=str)
# def embed(name: str):
#     """
#     Command embedded in cli.py.
    
#     Much longer stuff below here.
#     """
#     click.echo("Testing a command embedded directly in cli.py")

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
