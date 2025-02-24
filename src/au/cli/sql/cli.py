import click
from pathlib import Path
from pydoc import pager

from au.lib.click import AliasedGroup
from au.lib.common import get_double_line

from .query_file import get_query_files

@click.command(cls=AliasedGroup)
def sql():
    """Commands for working with SQL assignments."""
    pass

@sql.command()
@click.argument("path",required=True,
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option('-pc','--preserve-comments', is_flag=True,
              help="Set to override default behavior of removing single-line comments.")
def cat_sql(path: Path, preserve_comments: bool):
    """Concatenate all text from *.sql files and show them in a pager."""
    queries = get_query_files(path)
    if queries:
        all_sql = ''
        for query in queries:
            all_sql += get_double_line(query.query_name()) + '\n'
            with open(query.file, 'rt') as fi:
                for line in fi:
                    if preserve_comments or (line.strip() and not line.lstrip().startswith('--')):
                        all_sql += line
            all_sql += '\n'
        pager(all_sql)
    else:
        click.echo(f"\nNo SQL files found in {path}\n")
        # click.echo(click.get_current_context().get_help())

if __name__ == "__main__":
    sql()
