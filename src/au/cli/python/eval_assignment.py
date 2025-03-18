from typing import Dict
import logging
import os
import sys
from io import StringIO
from pathlib import Path
from datetime import datetime, date
import json

import pytest
import pylint.lint as lint
from pylint.reporters.json_reporter import JSON2Reporter

import click
from rich.console import Console

from au.common import draw_double_line
from git_wrap import GitRepo, Commit

from au.classroom import Assignment, Roster
from au.click import BasePath, AssignmentOptions, RosterOptions, DebugOptions
from au.common import draw_single_line
from au.common.datetime import get_friendly_timedelta

from .pytest_reporter import PytestResultsReporter
from .scoring import get_summary


logger = logging.getLogger(__name__)


RESULTS_FILE_NAME = ".eval_results.json"


def _json_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()


def _json_deserialize_hook(dct: Dict):
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                dct[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
    return dct


def retrieve_student_results(student_dir: Path) -> Dict:
    results_file = student_dir / RESULTS_FILE_NAME
    with open(results_file, "r") as fi:
        return json.load(fi, object_hook=_json_deserialize_hook)


@click.command("eval-assignment")
@click.argument("student_dir", type=BasePath(), required=True)
@AssignmentOptions(store=False).options
@RosterOptions(store=False, prompt=True).options
@click.option(
    "--student-name",
    type=str,
    help="If no roster is provided, you can provide the name of the student. "
    "If neither is provided, the name will just be STUDENT_DIR.",
)
@DebugOptions().options
def eval_assignment_cmd(
    student_dir: Path,
    assignment: Assignment,
    roster: Roster = None,
    student_name: str = None,
    **kwargs,
) -> None:
    """Run automated grading tests on a single student directory."""
    logging.basicConfig()

    draw_double_line()
    if assignment:
        print(assignment)
    else:
        logger.error(
            "Unable to find the requested assignment. Functionality will be limited."
        )
    draw_single_line()

    if roster:
        print(f"USING ROSTER: {roster.file.resolve()}")
    else:
        print("NOT USING ROSTER")

    draw_single_line()
    print()

    stu_name = student_name
    if roster and not stu_name:
        login = roster.get_login_for_dir(student_dir)
        stu_name = roster.login_student_map.get(login)

    student_results = eval_assignment(student_dir, stu_name, assignment)

    if student_results:
        draw_single_line(f"Summary Results")
        print(get_summary(student_results))
    else:
        print(f"No results for {stu_name}")


def eval_assignment(
    student_dir: Path, student_name: str, assignment: Assignment = None
) -> Dict[str, any]:
    """
    Run automated grading tests on a single student directory.
    """
    dir_name = student_dir.name
    os.chdir(student_dir)
    student_results: dict = {}

    student_results["name"] = student_name
    student_results["dir_name"] = dir_name
    if assignment:
        student_results["assignment_title"] = assignment.title
        student_results["assignment_deadline"] = assignment.deadline

    ###############################################################################
    # REPO CHECKS
    ###############################################################################

    console = Console()
    with console.status(
        f"Running Git Repository checks for {student_name}", spinner="bouncingBar"
    ) as status:
        try:
            # repo = Repo()
            repo = GitRepo()
            assert repo
        except:
            logger.error(f"No git repository found in {dir_name}")
            return None

        self_email = GitRepo.get_user_email()
        commits: list[Commit] = []
        for commit in repo.get_commits():
            # Skip the evaluator...best effort
            if commit.author_email == self_email:
                continue
            # First GitHub commit is considered the end of the list of student
            # commits
            if commit.committer_name == "GitHub":
                break
            commits.append(commit)

        student_results["num_commits"] = len(commits)
        if commits:
            commit = commits[0]
            if not student_name:
                student_results["name"] = commit.author_name
            student_results["commit_message"] = commit.message.strip()
            student_results["commiter_name"] = commit.author_name
            commit_date = commit.date
            student_results["commit_date"] = commit_date
            if assignment:
                past_due = commit_date - assignment.deadline
                if past_due.total_seconds() > 0:
                    student_results["past_due"] = get_friendly_timedelta(past_due)
        else:
            return None

    ###############################################################################
    # PYTEST
    ###############################################################################

    draw_single_line("pytest")

    pytest_reporter = PytestResultsReporter()

    keep_packages = [
        "_asyncio",
        "_contextvars",
        "_elementtree",
        "_pytest",
        "_ssl",
        "asyncio",
        "attr",
        "cmd",
        "code",
        "codeop",
        "contextvars",
        "faulthandler",
        "pdb",
        "pkgutil",
        "pyexpat",
        "pytest_metadata",
        "pytest_subtests",
        "readline",
        "ssl",
        "unittest",
        "xml",
    ]

    pretest_modules = [key for key in sys.modules.keys()]
    pretest_path = sys.path.copy()

    try:
        # run the tests and report
        pytest.main(
            ["--tb=no", "-q", "--timeout=1"],
            plugins=[pytest_reporter],
        )

        pytest_pct = round(pytest_reporter.results.pass_pct, 3)
        student_results["pytest_pct"] = pytest_pct
        student_results["pytest_results"] = pytest_reporter.results.as_dict()

    except Exception as ex:
        student_results["pytest_exception"] = ex
        logger.exception("Unexpected error running pytest")

    finally:
        posttest_modules = [key for key in sys.modules.keys()]
        for module_name in posttest_modules:
            if module_name in pretest_modules:
                continue
            package = module_name.split(".")[0]
            if package in keep_packages:
                continue
            del sys.modules[module_name]
        sys.path = pretest_path.copy()

    ###############################################################################
    # PYLINT
    ###############################################################################

    draw_single_line("pylint")
    status.update(status=f"Running pylint for {student_name}")

    lint_files = []
    lint_filenames = []
    cwd = Path.cwd()
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d[0] not in "._" and d[:4] != "test"]
        for file in files:
            if (
                file.endswith(".py")
                and not file.startswith(".")
                and not file.startswith("_")
                and not file.startswith("test_")
                and not file.endswith("_test.py")
            ):
                lint_filenames.append(file)
                lint_files.append(root + os.sep + file)

    if lint_files:
        print("Testing", *lint_filenames)

        lint_disabled = [
            "invalid-name",
            "missing-module-docstring",
            "missing-class-docstring",
            "missing-function-docstring",
            "trailing-whitespace",
            "missing-final-newline",
            "trailing-newlines",
            "unnecessary-negation",
            "wrong-import-order",
            "duplicate-code",
            "too-few-public-methods",
            "too-many-arguments",
            "too-many-locals",
            "too-many-statements",
            "bare-except",
            "f-string-without-interpolation",
            "chained-comparison",
            "consider-using-sys-exit",
            "singleton-comparison",
            "consider-using-max-builtin",
            # 'bad-indentation',
            "redefined-outer-name",
            "simplifiable-if-statement",
            "no-else-return",
            "inconsistent-return-statements",
        ]
        lint_args = []
        lint_args += ["--disable=" + ",".join(lint_disabled)]
        lint_args += lint_files
        pylint_output = StringIO()  # Custom open stream
        pylint_reporter = JSON2Reporter(pylint_output)

        try:
            lint.Run(lint_args, reporter=pylint_reporter, exit=False)
            pylint_results = json.loads(pylint_output.getvalue())
            pylint_pct = round(pylint_results["statistics"]["score"] / 10.0, 3)
            student_results["pylint_pct"] = pylint_pct
            if pylint_pct < 1:
                student_results["pylint_results"] = pylint_results
        except Exception as ex:
            student_results["pylint_exception"] = ex
            logger.exception("Unexpected error running pylint")
    else:
        logger.error("No files found to lint found")

    ###############################################################################
    # Save and return the test results data
    ###############################################################################

    with open(RESULTS_FILE_NAME, "w") as fi:
        json.dump(student_results, fi, indent=2, default=_json_serialize)

    return student_results


if __name__ == "__main__":
    eval_assignment_cmd()
