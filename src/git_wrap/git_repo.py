"""Contains the GitRepo class and related utility functions."""

from dataclasses import dataclass
from typing import Iterable, List, SupportsIndex
import sys
from datetime import datetime
import os
from textwrap import dedent
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class NotARepoError(ValueError):
    """Indicates that a specified directory is not a Git repository"""


class GitCommandError(Exception):
    """Indicates that a git command exited with a non-zero exit code"""


@dataclass
class Commit:
    """Basic dataclass describing a single Git commit."""

    hash: str
    message: str
    date: datetime
    author_name: str
    author_email: str
    committer_name: str


class GitRepo:
    """Basic wrapper around git for when GitPython is overkill."""

    def __init__(
        self,
        path: Path | str = ".",
        traverse_parents: bool = False,
        create: bool = False,
    ):
        path = Path(path).resolve()
        base = GitRepo.get_repository_root(path)
        if base:
            if traverse_parents or base == path:
                self.root_dir = base
                self.name = base.name
                return
        elif create:
            self.root_dir = path
            self.name = path.name
            self._git("init", "-b", "main")
            return
        root = " root" if not traverse_parents else ""
        raise NotARepoError(f"{path} is not a valid repository{root}")

    def __str__(self):
        return self.name

    @staticmethod
    def git(
        *args, path: Path | str = Path.cwd(), log_error: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute a single git command in the provided path."""
        path = Path(path)
        cmd = ["git", "--no-pager"]
        cmd.extend(args)
        prev_cwd = os.getcwd()
        try:
            os.chdir(path)
            return subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError:
            logger.exception(
                "Error trying to run `git` command. Git may not be installed."
            )
        except KeyboardInterrupt:
            sys.exit(1)
        except subprocess.CalledProcessError as ex:
            if log_error:
                err = f"""
                    COMMAND:    {ex.cmd}
                    CODE:       {ex.returncode}
                    OUTPUT:     {ex.output}
                    STDERR:     {ex.stderr}
                    """
                logger.error(dedent(err).strip())
            raise GitCommandError() from ex
        finally:
            os.chdir(prev_cwd)
        return None

    @staticmethod
    def get_repository_root(path: Path | str) -> Path:
        """
        Gets the base directory of a Git repository at `path` or None if it is
        not a repository.
        """
        path = Path(path).resolve()
        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")
        try:
            proc = GitRepo.git(
                "rev-parse", "--show-toplevel", path=path, log_error=False
            )
            root = Path(proc.stdout.strip())
            if root.is_dir() and path.exists():
                return root.resolve()
        except GitCommandError:
            pass
        return None

    @staticmethod
    def is_repository(path: Path | str) -> bool:
        """Determines whether `path` is a Git repository."""
        path = Path(path).resolve()
        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")
        return GitRepo.get_repository_root(path) is not None

    @staticmethod
    def is_repository_root(path: Path | str) -> bool:
        """Determines whether qpath` is at the root of a Git repository."""
        path = Path(path).resolve()
        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")
        root = GitRepo.get_repository_root(path)
        return root and root == path

    @staticmethod
    def clone(source_url: str, dest_dir: Path | str) -> None:
        """
        Clone a git repository from a source URL into a subdirectory `dest_dir`.
        If `dest_dir` does not exist, it will be created. If `dest_dir` is not
        empty, the command will fail.
        """
        dest_dir = Path(dest_dir).resolve()
        if dest_dir.exists():
            for _ in dest_dir.iterdir():
                raise FileExistsError(f"{dest_dir} is not empty")
        GitRepo.git("clone", source_url, str(dest_dir))

    @staticmethod
    def get_user_name() -> str:
        """Retrieve the current user's name from the global git config."""
        try:
            proc = GitRepo.git("config", "--global", "--get", "user.name")
            return proc.stdout.strip()
        except GitCommandError:
            return None

    @staticmethod
    def get_user_email() -> str:
        """Retrieve the current user's email from the global git config."""
        try:
            proc = GitRepo.git("config", "--global", "--get", "user.email")
            return proc.stdout.strip()
        except GitCommandError:
            return None

    def _git(self, *args, log_error: bool = True) -> subprocess.CompletedProcess:
        return GitRepo.git(*args, path=self.root_dir, log_error=log_error)

    def is_dirty(self, untracked_files: bool = True) -> bool:
        """Determine if a Git repository contains changed or untracked files."""
        if untracked_files:
            proc = self._git("status", "-s")
        else:
            proc = self._git("status", "-s", "-u", "no")
        output = proc.stdout.strip() + proc.stderr.strip()
        if output:
            return True
        else:
            return False

    def needs_pull(self) -> bool:
        """Check whether remote is ahead of local."""
        proc = self._git("fetch", "--dry-run")
        output = proc.stdout.strip() + proc.stderr.strip()
        if output:
            return True
        else:
            return False

    def pull(self) -> None:
        """Pull changes from the default Git repository remote."""
        proc = self._git("fetch")
        output = proc.stdout.strip() + proc.stderr.strip()
        if not output:
            return False
        self._git("merge")
        return True

    def add(self, files: Iterable[Path | str] = None) -> None:
        """Run `git add` to stage files. If files is empty, add `.` (all)."""
        args = []
        if files:
            for file in files:
                file = Path(file)
                if file.exists() and file.is_relative_to(self.root_dir):
                    files.append(file.relative_to(self.root_dir))
        if not args:
            args.append(".")
        self._git("add", *args)

    def commit(self, message: str) -> None:
        """Commit any staged changes using the provided message."""
        if not message:
            raise ValueError("`messageq` cannot be empty.")
        self._git("commit", "-m", message)

    def push(self, remote: str = None, branch: str = None):
        """Push changes to the default Git repository remote."""
        if not remote:
            self._git("push")
        else:
            if not branch:
                raise ValueError(
                    "both remote and branch are required for push --set-upstream <remote> <branch>"
                )
            self._git("push", "--set-upstream", remote, branch)

    def get_commits(self, limit: int = None, skip: int = None) -> List[Commit]:
        """
        Return commits for the current branch. By default, all will be returned
        as a list. Alternatively a limit (and optionall a skip offset) may be
        specified to reduce the number of commits returned.
        """
        args = ["log", "--format=h:%t%nm:%s%nd:%aI%na:%an%ne:%aE%nc:%cn%n--"]
        if limit:
            args.append(f"--max-count={limit}")
        if skip:
            args.append(f"--skip={skip}")

        proc = self._git(*args)
        raw_commits = proc.stdout.split("\n--")
        commits: List[Commit] = []
        for raw_commit in raw_commits:
            commit_hash = message = date = author_name = author_email = (
                committer_name
            ) = None
            lines = raw_commit.strip().splitlines()
            if not len(lines) == 6:
                continue
            for line in lines:
                key: str = line[0]
                val: str = line[2:]
                match key:
                    case "h":
                        commit_hash = val.strip()
                    case "m":
                        message = val.strip()
                    case "d":
                        date = datetime.fromisoformat(val.strip())
                    case "a":
                        author_name = val.strip()
                    case "e":
                        author_email = val.strip()
                    case "c":
                        committer_name = val.strip()
            commit = Commit(
                commit_hash, message, date, author_name, author_email, committer_name
            )
            commits.append(commit)
        return commits


def has_git_repo_subdirs(path: str | Path) -> bool:
    """Determine if `path` contains subdirectories that are Git repositories."""
    path = Path(path).resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")
    for sub_path in path.iterdir():
        if sub_path.is_dir():
            if GitRepo.is_repository(sub_path):
                return True
    return False


def get_git_dirs(path: str | Path) -> List[Path]:
    """Return all subdirectories  of `path` that contain Git repositories."""
    path = Path(path).resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")
    git_dirs = []
    for sub_path in path.iterdir():
        if sub_path.is_dir():
            if GitRepo.is_repository(sub_path):
                git_dirs.append(sub_path)
    return git_dirs


def get_git_repos(path: str | Path) -> List[GitRepo]:
    """Return all git repositories that are subdirectories of `path`."""
    path = Path(path).resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")
    repos = []
    for sub_path in path.iterdir():
        if sub_path.is_dir():
            try:
                repos.append(GitRepo(sub_path))
            except NotARepoError:
                pass
    return repos


def get_dirty_repos(path: str | Path, untracked_files: bool = True) -> List[GitRepo]:
    """
    Return a list of GitRepo objects for all subdirectories of `path` if and
    only if the Git repository has changed or untracked files.
    """
    repos = get_git_repos(path)
    return [repo for repo in repos if repo.is_dirty(untracked_files=untracked_files)]
