from typing import List
from dataclasses import dataclass
from pathlib import Path
import re

_QUERY_FILE_PATTERN = re.compile(r"^([^\d]*)?(\d+)?(.*)?(.sql)$")


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
        return self.prefix + "0" * diff + self.num + self.suffix

    @staticmethod
    def parse(file: Path):
        match = _QUERY_FILE_PATTERN.search(file.name)
        if not match:
            return None

        groups = match.groups()
        prefix = groups[0] if groups[0] else ""
        num = groups[1] if groups[1] else ""
        suffix = groups[2] if groups[2] else ""
        extension = groups[3] if groups[3] else ""
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
