import logging
from pathlib import Path
from pprint import pformat

import click
from rich.console import Console

from git_wrap import get_git_dirs

from au.click import BasePath, AssignmentOptions, RosterOptions, DebugOptions
from au.classroom import Assignment, Roster
from au.common import draw_double_line, draw_single_line

from .eval_assignment import retrieve_student_results, eval_assignment
from .gen_feedback import (
    gen_feedback,
    get_summary,
    ScoringParams,
    DEFAULT_FEEDBACK_FILE_NAME,
)


logger = logging.getLogger(__name__)


@click.command()
@click.argument("root_dir", type=BasePath(), default=".")
@AssignmentOptions().options
@RosterOptions(prompt=True).options
@click.option(
    "-se", "--skip_eval", is_flag=True, help="set to bypass running the evaluations"
)
@click.option(
    "-sf", "--skip_feedback", is_flag=True, help="set to bypass generating feedback"
)
@click.option(
    "--feedback-filename",
    type=str,
    default=DEFAULT_FEEDBACK_FILE_NAME,
    show_default=True,
    help="name of markdown file to generate",
)
@click.option(
    "-o",
    "--overwrite-feedback",
    is_flag=True,
    help="set to override default behavior of not overwriting feedback files",
)
@click.option(
    "-max",
    "--max-score",
    type=float,
    default=10,
    show_default=True,
    help="the maximum score for this assignment",
)
@click.option(
    "-ptw",
    "--pytest-weight",
    type=float,
    default=1.0,
    show_default=True,
    help="the weight to apply to pytest when calculating the overall score (0 to 1)",
)
@click.option(
    "-plw",
    "--pylint-weight",
    type=float,
    default=0.0,
    show_default=True,
    help="the weight to apply to pylint when calculating the overall score (0 to 1)",
)
@DebugOptions().options
def quick_grade(
    root_dir: Path,
    assignment: Assignment = None,
    roster: Roster = None,
    skip_eval: bool = False,
    skip_feedback: bool = False,
    feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
    overwrite_feedback: bool = False,
    max_score: int = 10,
    pytest_weight: float = 1.0,
    pylint_weight: float = 0.0,
    **kwargs,
) -> None:
    """Run tests and generate feedback for all subdirectories of ROOT_DIR.

    This is essentially the same as:

    \b
        for SUBDIR in ROOT_DIR
            au python eval-assignment SUBDIR
            au python gen-feedback SUBDIR

    If ROOT_DIR is not provided, then the current working directory will be
    assumed.
    """
    logging.basicConfig()

    draw_double_line()
    if assignment:
        print(assignment)
    else:
        logger.error(
            "Unable to find the requested assignment. Functionality will be limited."
        )
    draw_single_line()

    dir_student_map = None
    if roster:
        print(f"USING ROSTER: {roster.file.resolve()}")
        login_student_map = roster.login_student_map
        logger.debug(pformat(login_student_map))
        dir_student_map = roster.get_dir_student_map(root_dir)
        logger.debug(pformat(dir_student_map))
    else:
        print("NOT USING ROSTER")

    draw_single_line()
    print()

    #################################################################
    # TODO: Pull feedback filename and scoring params from settings

    scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)

    ###############################################################################
    # PROCESS DIRS
    ###############################################################################

    console = Console()
    with console.status(
        status="Finding assignment directories in {root_dir}", spinner="bouncingBall"
    ):
        student_repos = get_git_dirs(root_dir)
        student_repos.sort()

    print(f"Processing {len(student_repos)} assignment directories")

    for student_repo in student_repos:

        print()
        dir_name = student_repo.name
        draw_double_line(f"Processing {dir_name}")

        student_name = None
        if dir_student_map and dir_name in dir_student_map:
            student_name = dir_student_map[dir_name]

        dir_path = (root_dir / student_repo).resolve()
        if skip_eval:
            try:
                student_results = retrieve_student_results(dir_path)
            except:
                print(f"SKIPPING: No results file found. Have you run the tests yet?")
                continue
        else:
            student_results = eval_assignment(dir_path, student_name, assignment)

        if not student_results:
            continue

        if not skip_feedback:
            draw_single_line(f"Generating {feedback_filename}")

            try:
                scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)
                gen_feedback(
                    student_results,
                    student_repo,
                    feedback_filename,
                    scoring_params,
                    overwrite_feedback,
                )
            except:
                logging.exception(
                    "An unexpected error occurred generating {student_repo / feedback_filename}"
                )

                print(f"done generating {feedback_filename}")

        print(get_summary(student_results, scoring_params))
        draw_double_line()
        print()


if __name__ == "__main__":
    quick_grade()
