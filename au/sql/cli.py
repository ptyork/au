import click
from au.lib.click.AliasedGroup import AliasedGroup

@click.command("sql", short_help="Commands for working with SQL assignments.", cls=AliasedGroup)
def main():
    pass

@main.command()
@click.argument("path", required=False, type=click.Path(resolve_path=True))
def do_something(path):
    print(f"RUH TEST COMMAND: {path}")
