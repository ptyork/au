import click

from io import TextIOWrapper
from pathlib import Path
from pprint import pformat
from yaspin import yaspin

from au.lib.classroom import Classroom, Assignment
from au.lib.classroom import choose_classroom, get_assignment, choose_assignment
from au.lib.git import get_git_dirs
from au.lib.common.terminal import draw_double_line, draw_single_line
from au.lib.common.csv import dict_from_csv
from au.lib.common.label_dir import FileType, label_dir

from .eval_assignment import retrieve_student_results, eval_assignment
from .gen_feedback import gen_feedback, get_summary, ScoringParams, DEFAULT_FEEDBACK_FILE_NAME

import logging
_base_logging_level = logging.INFO
logging.basicConfig(level=_base_logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(_base_logging_level)

@click.command()
@click.argument("root_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("-r", "--roster", type=click.File(),
              help="provide the classroom roster to retrieve actual student names")
@click.option("-a", "--assignment-id", type=int,
              help="the integer classroom id for the assignment; will prompt for the classroom and assignment if not provided")
@click.option("-se", "--skip_eval", is_flag=True, help="set to bypass running the evaluations")
@click.option("-sf", "--skip_feedback", is_flag=True, help="set to bypass generating feedback")
@click.option("--feedback-filename", type=str, default=DEFAULT_FEEDBACK_FILE_NAME, show_default=True,
              help="name of markdown file to generate")
@click.option("-o", "--overwrite-feedback", is_flag = True,
              help="set to override default behavior of not overwriting feedback files")
@click.option("-max", "--max-score", type=float, default=10, show_default=True,
              help="the maximum score for this assignment")
@click.option("-ptw", "--pytest-weight", type=float, default=1.0, show_default=True,
              help="the weight to apply to pytest when calculating the overall score (0 to 1)")
@click.option("-plw", "--pylint-weight", type=float, default=0.0, show_default=True,
              help="the weight to apply to pylint when calculating the overall score (0 to 1)")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
def quick_grade(root_dir: Path,
                roster: TextIOWrapper|Path = None,
                assignment_id: int = None,
                skip_eval: bool = False,
                skip_feedback: bool = False,
                feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
                overwrite_feedback: bool = False,
                max_score: int = 10,
                pytest_weight: float = 1.0,
                pylint_weight: float = 0.0,
                debug: bool = False,
                quiet: bool = False) -> None:

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)

    dir_student_map = None

    if roster:
        try:
            id_student_map = dict_from_csv(roster, 'github_username', 'identifier')
            logger.debug(pformat(id_student_map))
            dir_student_map = label_dir(id_student_map, root_dir, FileType.DIRECTORY)
            logger.debug(pformat(id_student_map))

        except Exception as ex:
            logger.warning(f"Error encountered while processing roster: {ex}")

    scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)


    ###############################################################################
    # GET ASSIGNMENT DETAILS
    ###############################################################################

    if assignment_id:
        assignment = get_assignment(assignment_id)
    else:
        classroom: Classroom = choose_classroom()
        assignment: Assignment = choose_assignment(classroom)

    draw_single_line()

    if assignment:
        print(assignment)
    else:
        logger.error("Unable to find the requested assignment. Functionality will be limited.")

    draw_single_line()
    print()

    ###############################################################################
    # PROCESS DIRS
    ###############################################################################

    with yaspin(text=f"Finding assignment directories in {root_dir}").aesthetic:
        student_repos = get_git_dirs(root_dir)
        student_repos.sort()

    print(f'Processing {len(student_repos)} assignment directories')

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
                gen_feedback(student_results, student_repo, feedback_filename, scoring_params, overwrite_feedback)
            except:
                logging.exception('An unexpected error occurred generating {student_repo / feedback_filename}')

                print(f'done generating {feedback_filename}')

        print(get_summary(student_results, scoring_params))
        draw_double_line()
        print()


if __name__ == '__main__':
    quick_grade()