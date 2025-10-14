import logging
from pathlib import Path

import click
from rich.console import Console

from git_wrap import GitRepo, get_git_dirs
from git_wrap.git_repo import GitCommandError
from au.click import BasePath
from au.common import draw_double_line


logger = logging.getLogger(__name__)


@click.command()
@click.argument("root_dir", type=BasePath())
@click.argument("command", type=click.UNPROCESSED, nargs=-1)
def recursive_git(
    root_dir: Path,
    command: str,
) -> None:
    """Run a git COMMAND on all repositories in ROOT_DIR.

    This will search ROOT_DIR for all git repositories (directories containing a
    .git subdirectory) and run the specified git COMMAND in each repository.

    COMMAND:
    
     - should be a valid git command, such as 'status', 'pull', 'fetch', etc.
     - should NOT include the 'git' prefix
     - is executed after changing directory to each repository
     - all arguments after COMMAND are passed directly to git
    """
    logging.basicConfig()

    console = Console()
    with console.status(
        status="Finding repositories in {root_dir}", spinner="bouncingBall"
    ):
        repo_dirs = get_git_dirs(root_dir)

    print(f"Processing {len(repo_dirs)} repositories")

    for repo_dir in repo_dirs:

        print()
        dir_name = repo_dir.name

        draw_double_line(f"Processing {dir_name}")
        print("> git", *command)

        try:
            result = GitRepo.git(*command, path=repo_dir)
            if result:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
        except GitCommandError:
            pass # Already logged
        except Exception:
            logger.exception(
                "Failed to run 'git {command}' in {dir_name}"
            )
