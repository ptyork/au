from typing import List
from dataclasses import dataclass
import click
from pathlib import Path
from pydoc import pager
import re

from au.lib.click.AliasedGroup import AliasedGroup
from au.lib.common.terminal import get_line
from au.lib.common.box_chars import BoxChars

_query_file_re = re.compile(r'^([^\d]*)?(\d+)?(.*)?(.sql)$')

@dataclass
class QueryFile:
    file: Path
    prefix: str
    num: str
    suffix: str
    extension: str

    def query_name(self):
        return f"{self.prefix}{self.num}{self.suffix}"

    def file_name(self):
        return f"{self.prefix}{self.num}{self.suffix}{self.extension}"

    def sort_name(self, num_zeros: int) -> str:
        if not self.num:
            return self.query_name()
        diff = num_zeros - len(self.num)
        return self.prefix + '0'*diff + self.num + self.suffix
    
    @staticmethod
    def parse(file: Path):
        match = _query_file_re.search(file.name)
        if not match:
            return None
        
        groups = match.groups()
        prefix = groups[0] if groups[0] else ''
        num = groups[1] if groups[1] else ''
        suffix = groups[2] if groups[2] else ''
        extension = groups[3] if groups[3] else ''
        return QueryFile(file, prefix, num, suffix, extension)


def get_query_files(path: Path) -> List[QueryFile]:
    queries: List[QueryFile] = []
    for file in path.iterdir():
        q = QueryFile.parse(file)
        if q:
            queries.append(q)
    
    if queries:
        max_q_len = max([len(q.num) for q in queries])
        queries.sort(key=lambda q: q.sort_name(max_q_len))

    return queries

@click.command(cls=AliasedGroup)
def sql():
    """Commands for working with SQL assignments."""
    pass

@sql.command()
@click.argument("path",default=Path.cwd(),
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option('-pc','--preserve-comments', is_flag=True,
              help="Set to override default behavior of removing single-line comments.")
def cat_sql(path: Path, preserve_comments: bool):
    """Concatenate all text from *.sql files and show them in a pager."""
    queries = get_query_files(path)
    if queries:
        all_sql = ''
        for query in queries:
            all_sql += get_line(BoxChars.DOUBLE_HORIZONTAL, query.query_name()) + '\n'
            with open(query.file, 'rt') as fi:
                for line in fi:
                    if preserve_comments or (line.strip() and not line.lstrip().startswith('--')):
                        all_sql += line
            all_sql += '\n'
        pager(all_sql)
    else:
        click.echo("\nNo SQL files found in current directory.\n")
        click.echo(click.get_current_context().get_help())

if __name__ == "__main__":
    sql()
