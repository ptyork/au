#!/usr/bin/env python3

from typing import List

import argparse
import logging
import os
from pathlib import Path
from pprint import pformat

from gh_classroom_types import Course, Assignment
from gh_classroom_util import get_course, get_assignment, choose_assignment
from terminal_util import draw_double_line, draw_single_line
from csv_dir_map import get_dir_map

from gh_run_tests import retrieve_student_results, run_tests
from gh_gen_feedback import gen_feedback_file, print_summary, ScoringParams
from gh_util import get_git_dirs

_base_logging_level = logging.WARNING

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(_base_logging_level)

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

parser.description = '''
'''

parser.add_argument("root_dir", type=str, help="the directory containing the repositories to grade")
parser.add_argument("--csv-file", help="Github Classroom roster file, containing real name and student name", type=str, default=None)
parser.add_argument("-st", "--skip-tests", help="set to skip the running of the tests, instead using cached results", action="store_true")
parser.add_argument("-sf", "--skip-feedback", help="set to skip generating the feedback markdown files", action="store_true")
parser.add_argument("--feedback-file", help="name of markdown file to generate (default=`FEEDBACK.md`)", type=str, default='FEEDBACK.md')
parser.add_argument("-ff", "--force-feedback", help="set to override default behavior of not overwriting feedback files", action="store_true")
parser.add_argument("-max", "--max-score", help="the maximum score for this assignment (default=10)", type=float, default=10)
parser.add_argument("-ptw", "--pytest-weight", help="the weight to apply to the pytest scores when calculating the overall score (0 to 1; default=1)", type=float, default=1)
parser.add_argument("-plw", "--pylint-weight", help="the weight to apply to the pylint scores when calculating the overall score (0 to 1; default=0)", type=float, default=0)
parser.add_argument("-a", "--assignment-id", help="the integer course id for the assignment; will prompt for the course and assignment if not provided", type=int, default=None)
parser.add_argument("-d", "--debug", help="set to enable detailed output", action="store_true")

args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)


###############################################################################
# SETUP AND VALIDATE ARGUMENTS
###############################################################################

root_dir = Path(os.path.abspath(args.root_dir))

if not root_dir.is_dir():
    logger.error(f"{root_dir} is not a valid directory")
    exit(1)


if args.csv_file:
    try:
        id_student_map, dir_student_map, missing_ids = get_dir_map(root_dir, args.csv_file, 1, 0)
        logger.debug(pformat(dir_student_map))
    except Exception as ex:
        logger.error(f"Error encountered while processing {args.csv_file}: {ex}")
        exit(1)


max_score = args.max_score
pytest_weight = args.pytest_weight
pylint_weight = args.pylint_weight
scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)


###############################################################################
# GET ASSIGNMENT DETAILS
###############################################################################

if args.assignment_id:
    course, assignment = get_assignment(args.assignment_id)
else:
    course: Course = get_course()
    if course:
        assignment: Assignment = choose_assignment(course)

draw_single_line()

if assignment:
    print(course)
    print(assignment)
else:
    logger.error("Unable to find the requested assignment. Functionality will be limited.")

###############################################################################
# PROCESS DIRS
###############################################################################

student_repos = get_git_dirs(root_dir)
student_repos.sort()

all_student_results = []

for student_repo in student_repos:

    dir_name = student_repo.name
    draw_double_line(f"Processing {dir_name}")

    student_name = None
    if dir_student_map and dir_name in dir_student_map:
        student_name = dir_student_map[dir_name]

    dir_path = (root_dir / student_repo).resolve()
    if args.skip_tests:
        try:
            student_results = retrieve_student_results(dir_path)
        except:
            print(f"SKIPPING: No results file found. Have you run the tests yet?")
            continue
    else:
        student_results = run_tests(dir_path, assignment, student_name)

    if not student_results:
        continue

    all_student_results.append(student_results)

    feedback_file_name: str = args.feedback_file
    if not args.skip_feedback:
        draw_single_line("Generating {feedback_file_name}")

        feedback_file_path = dir_path / feedback_file_name

        if not args.force_feedback and feedback_file_path.exists():
            print("SKIPPING: feedback file exists and --force-feedback not set")
        else:
            try:
                gen_feedback_file(student_results, feedback_file_path, scoring_params)
            except:
                logging.exception('An unexpected error occurred generating {feedback_file_path}')

            print(f'done generating {feedback_file_name}')

    draw_single_line("Summary")
    print_summary(student_results, scoring_params)
    draw_double_line()
    print()



