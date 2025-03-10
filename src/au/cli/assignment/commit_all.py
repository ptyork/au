import sys
from pathlib import Path
import logging

import click
from rich.console import Console

from f_table import BasicScreenStyle, get_table
from git_wrap import get_git_repos

from au.click import DebugOptions, BasePath


logger = logging.getLogger(__name__)


@click.command()
@click.argument("root_dir", type=BasePath(resolve_path=True), default=".")
@click.option(
    "-m",
    "--message",
    prompt=True,
    type=str,
    default="Posting feedback",
    help="the message to apply to all `git commit` calls",
)
@click.option(
    "-p",
    "--preview",
    is_flag=True,
    help="set to show changes without actually making them",
)
@DebugOptions().options
def commit_all(
    root_dir: Path,
    message: str = "Posting feedback",
    preview: bool = False,
    quiet: bool = False,
    debug: bool = False,
):
    """Commit and push all "dirty" student repos in ROOT_DIR.

    Iterate over all immediate subdirectories of ROOT_DIR. If it is found to be
    a Git repository and if it contains changes, then:

    \b
        + add all changes
        + commit using --message
        + push all changes to the remote

    If ROOT_DIR is not provided, then the current working directory will be
    assumed.

    If the `--message` argument is not provided, the script will prompt for one.
    """
    logging.basicConfig()

    skips = []
    commits = []
    errors = []

    console = Console()
    with console.status(
        "Finding all local Git repositories", spinner="bouncingBall"
    ) as status:

        all_repos = get_git_repos(root_dir)

        for repo in all_repos:
            status.update(status=f"{repo.name}: Checking for changes")
            if repo.name.startswith("_"):
                skips.append([repo.name, "special directory"])
                continue

            if not repo.is_dirty():
                skips.append([repo.name, "no changes to commit"])
                continue

            if preview:
                commits.append([repo.name, "WOULD COMMIT"])
                continue

            try:
                status.update(status=f"{repo.name}: git pull")
                repo.pull()

                status.update(status=f"{repo.name}: git add .")
                repo.add()

                status.update(status=f"{repo.name}: git commit -m {message}")
                repo.commit(message)

                status.update(status=f"{repo.name}: git push")
                repo.push()

                commits.append([repo.name, "COMMITTED"])
            except Exception as ex:
                logger.exception("Error occurred running git command")
                errors.append([repo.name, str(ex)])

    # Print a summary
    if quiet:
        all_dirs = errors
    else:
        all_dirs = commits + skips + errors
    all_dirs.sort()

    if not all_dirs:
        print("No repositories found")
        sys.exit(0)

    print(get_table(all_dirs, col_defs=["", "A"], style=BasicScreenStyle()))

    summary = []
    summary.append([f"Root Directory", root_dir])
    if preview:
        summary.append([f"Repositories to Commit", len(commits)])
    else:
        summary.append([f"Repositories Pushed", len(commits)])
    summary.append([f"Directories Skipped", len(skips)])
    summary.append([f"Errors Encountered", len(errors)])
    print(get_table(summary, style=BasicScreenStyle()))


if __name__ == "__main__":
    commit_all()
