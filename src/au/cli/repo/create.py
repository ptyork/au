from pathlib import Path
from shutil import rmtree
import sys

import click

from git_wrap import GitRepo
from au.classroom import gh, gh_api, choose_classroom, get_classroom, choose_assignment
from au.click import BasePath
from au.common import get_double_line


@click.command()
@click.argument("path", type=BasePath(resolve_path=True, exists=False))
@click.option(
    "--classroom-id",
    type=int,
    help="The integer id for the classroom. If not provided, will prompt for it interactively.",
)
@click.option(
    "--owner",
    type=str,
    help="If not for a classroom, then specify the owner / organization.",
)
@click.option(
    "--name",
    type=str,
    help="The remote GitHub repository name if other than PATH's name.",
)
@click.option(
    "--gitignore",
    type=str,
    help="The gitignore template to use for the repository.",
)
@click.option(
    "--public",
    is_flag=True,
    help="Make the repository public (default is private)",
)
@click.option(
    "--force-init",
    is_flag=True,
    help="Remove any existing .git/ dir and reinitialize the repo.",
)
def create(
    path: Path,
    classroom_id: int = None,
    owner: str = None,
    name: str = None,
    gitignore: str = None,
    public: bool = False,
    force_init: bool = False,
):
    """Create a new Git and GitHub repo in PATH.

    This command automates a number of tedious manual tasks required to create
    and initialize a new git repo and connect it to a new repository on GitHub.
    The repository is assumed to be for a specified classroom. However, the
    `--owner` option can be specified to define an owner that is not the
    organization associated with a GitHub Classroom.

    The process is as follows:

    \b
        - If PATH does not exist, it will be created locally.
        - If PATH is not currently a git repository, run `git init` to
          initialize PATH as the base of a new git repo.
        - Add README.md and .gitignore if not already existing
        - Stage and commit any new or changed files in PATH
        - Create a new GitHub repository and push all commits

    Explicit error conditions:

    \b
        - If PATH exists, it must be a directory.
        - PATH cannot be a subdirectory of an existing Git repository.
        - If the GitHub repository already exists.
    """
    if path.parent.exists() and GitRepo.is_repository(path.parent):
        print(path.parent)
        print(f"ERROR: {path} is already part of an existing git repository")
        sys.exit(1)

    if path.exists() and not path.is_dir():
        print(f"ERROR: {path} is not a directory.")
        sys.exit(1)

    name = name if name else path.name

    if not owner:
        if not classroom_id:
            classroom = choose_classroom()
            if classroom:
                classroom_id = classroom.id
        if classroom_id:
            # need more details to get org anyway, so always make second call
            classroom = get_classroom(classroom_id)
            if not classroom:
                print(f"ERROR: no classroom found with id {classroom_id}.")
                sys.exit(1)
            owner = classroom.organization.login

    if not owner:
        print("ERROR: cannot create a GitHub repository without an owner.")

    # make sure the GitHub repository does not already exist
    if gh_api(f"repos/{owner}/{name}"):
        print(f"GitHub repository {owner}/{name} already exists")

    readme_path = path / "README.md"
    gitignore_path = path / ".gitignore"
    gitignore_template = None

    if not gitignore and not gitignore_path.exists():
        # TODO: Change to confirm
        print(
            "ERROR: Won't commit a repository without a .gitignore. "
            "Specify a template using --gitignore or create one manually."
        )
        sys.exit(1)
    elif gitignore and not gitignore_path.exists():
        gitignore_template = gh_api(f"gitignore/templates/{gitignore}")
        if not gitignore_template:
            print(f"ERROR: unable to find gitignore template {gitignore}")
            sys.exit(1)
    elif gitignore:
        print(f"WARNING: .gitignore already exists; ignoring --gitignore {gitignore}")

    if not path.exists():
        new_repo = True
        path.mkdir()
    elif force_init:
        new_repo = True
        rmtree(path / ".git", ignore_errors=True)
    else:
        new_repo = not GitRepo.is_repository(path)

    if gitignore_template:
        with open(gitignore_path, "w") as fi:
            fi.write(gitignore_template["source"])

    if not readme_path.exists():
        with open(readme_path, "w") as fi:
            fi.write(f"# {name}\n")

    repo = GitRepo(path, create=True)
    if repo.is_dirty():
        repo.add()
        if new_repo:
            repo.commit("initial commit")
        else:
            repo.commit("push to GitHub")

    pub_priv = "--public" if public else "--private"
    gh(
        "repo",
        "create",
        f"{owner}/{name}",
        pub_priv,
        "--source",
        str(path),
        "--remote",
        "origin",
        "--disable-issues",
        "--disable-wiki",
        "--push",
    )

    # TODO: Add --make-template flag
    # gh api --method=PATCH /repos/au-aist2110-25sp-co1/proj01-template -F "is_template=true"
