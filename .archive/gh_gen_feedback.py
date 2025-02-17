#!/usr/bin/env python3

from typing import Dict
from dataclasses import dataclass
from datetime_util import get_friendly_local_datetime

import logging
import os
from pathlib import Path
from textwrap import wrap, indent

logger = logging.getLogger(__name__)


@dataclass
class ScoringParams:
    max_score: float = 10
    pytest_weight: float = 1
    pylint_weight: float = 0


@dataclass
class Score:
    pytest_pct: float
    pylint_pct: float
    overall_score: float


def get_student_scores(student_results: Dict, scoring_params: ScoringParams = ScoringParams()) -> Score:
    # Calculate score
    max = scoring_params.max_score
    pt_pct = student_results.setdefault('pytest_pct', 0)
    pt_weight = scoring_params.pytest_weight
    pl_pct = student_results.setdefault('pylint_pct', 0)
    pl_weight = scoring_params.pylint_weight
    total_score = round(max * ((pt_pct * pt_weight) + (pl_pct * pl_weight)), 2)

    return Score(pt_pct, pl_pct, total_score)


def print_summary(student_results: Dict, scoring_params: ScoringParams) -> None:
    scores = get_student_scores(student_results, scoring_params)
    print(f"│ Student Name        │ {student_results['name']}")
    print(f"│ LastCommit Date     │ {get_friendly_local_datetime(student_results['commit_date'])}")
    print(f"│ Last Commit Author  │ {student_results['commiter_name']}")
    print(f"│ Last Commit Message │ {student_results['commit_message']}")
    print(f"│ Total Commit Count  │ {student_results['num_commits']}")
    print(f"│ Functionality Score │ {scores.pytest_pct*100:.4g}% (weight: {scoring_params.pytest_weight*100:.4g}%)")
    print(f"│ Code Style Score    │ {scores.pylint_pct*100:.4g}% (weight: {scoring_params.pylint_weight*100:.4g}%)")
    print(f"│ Calculated Score    │ {scores.overall_score:g} / {scoring_params.max_score:g}")
    past_due = student_results.setdefault("past_due", None)
    if past_due:
        print(f"│ Past Due            │ {past_due}")


def get_feedback_file_score(feedback_file_path: Path) -> str:
    '''
    Returns score as string in case it has been annotated in the feedback file.
    '''
    score = None
    with open(feedback_file_path, 'r') as fi:
        for line in fi:
            if line.startswith('| Final Score'):
                parts = line[2:].split('|')
                score = parts[1].strip()
                break
    return score


def gen_feedback_file(student_results: Dict, feedback_file_path: Path, scoring_params: ScoringParams = ScoringParams()):

    scores = get_student_scores(student_results, scoring_params)

    with open(feedback_file_path, 'w') as fi:
        def wl(txt = ''):
            fi.write(str(txt) + '\n')

        wl('# Assignment Feedback')
        wl()
        wl( '|                     |                          |')
        wl( '| ------------------- | ------------------------ |')
        wl(f"| Student Name        | {student_results['name']}")
        if 'assignment_title' in student_results:
            wl(f"| Assignment Title    | {student_results['assignment_title']}")
            wl(f"| Deadline            | {get_friendly_local_datetime(student_results['assignment_deadline'])}")
        wl(f"| Last Commit Date    | {get_friendly_local_datetime(student_results['commit_date'])}")
        wl(f"| Last Commit Author  | {student_results['commiter_name']}")
        wl(f"| Last Commit Message | {student_results['commit_message']}")
        wl(f"| Total Commit Count  | {student_results['num_commits']}")
        wl(f"| Functionality Score | {scores.pytest_pct*100:.4g}% (weight: {scoring_params.pytest_weight*100:.4g}%)")
        wl(f"| Code Style Score    | {scores.pylint_pct*100:.4g}% (weight: {scoring_params.pylint_weight*100:.4g}%)")
        wl(f"| Calculated Score    | {scores.overall_score:g} / {scoring_params.max_score:g}")
        past_due = student_results.setdefault("past_due", None)
        if past_due:
            wl(f"| Past Due            | {past_due}")
        wl(f"| Final Score         | {scores.overall_score:g}")
        wl()
        wl()
        wl('-'*80)
        wl('## Grader Comments:')
        wl()
        wl()
        wl()

        if 'pytest_results' in student_results:
            wl()
            wl('-'*80)
            wl('## Functionality Feedback (pytest)')
            wl('-'*80)
            wl('```')
            test: Dict
            for test in student_results['pytest_results']['tests']:
                pass_pct = test['pass_pct']
                if pass_pct < 1:
                    full_name = test['name']
                    name_parts = full_name.split('::')
                    test_name = f"{name_parts[1]}: {name_parts[2].replace('_', ' ')}"
                    message = test['message']
                    wl(f"{test_name}")
                    wl(indent(message, '    '))
                    wl()
                    wl(' •' * 40)
                    wl()


            # wl(pformat(student_results['pytest_results']))
            wl('```')

        if 'pylint_results' in student_results:
            wl()
            wl('-'*80)
            wl('## Code Style Feedback (pylint)')
            wl()
            wl('```')
            msg: Dict
            for msg in student_results['pylint_results']['messages']:
                path = msg.setdefault('path', 'General Message')
                line = msg.setdefault('line', 0)
                line_str = f" line: {line}" if line else ""
                col = msg.setdefault('col', 0)
                col_str = f" col: {col}" if col else ""
                id = msg.setdefault('messageId', "No ID")
                message = msg.setdefault('message', "No message provided")
                wl(f"{path}{line_str}{col_str} ({id}):")
                wl('\n'.join(wrap(message, 80, initial_indent="    ", subsequent_indent="    ")))
                wl()
                wl(' •' * 40)
                wl()

            # wl(pformat(student_results['pylint_results']))
            wl('```')


if __name__ == "__main__":

    import argparse
    from gh_run_tests import retrieve_student_results

    _base_logging_level = logging.WARNING

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(_base_logging_level)


    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.description = '''
    '''

    parser.add_argument("student_dir", type=str, help="the directory containing the student repository")
    parser.add_argument("--feedback-file", help="name of markdown file to generate (default=`FEEDBACK.md`)", type=str, default='FEEDBACK.md')
    parser.add_argument("-ff", "--force-feedback", help="set to override default behavior of not overwriting feedback files", action="store_true")
    parser.add_argument("-max", "--max-score", help="the maximum score for this assignment (default-10)", type=float, default=10)
    parser.add_argument("-ptw", "--pytest-weight", help="the weight to apply to the pytest scores when calculating the overall score (0 to 1; default=0.9)", type=float, default=1)
    parser.add_argument("-plw", "--pylint-weight", help="the weight to apply to the pylint scores when calculating the overall score (0 to 1; default=0.1)", type=float, default=0)
    parser.add_argument("-d", "--debug", help="set to enable detailed output", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    student_dir = Path(os.path.abspath(args.student_dir))

    if not student_dir.is_dir():
        logger.error(f"{student_dir} is not a valid directory")
        exit(1)

    max_score = args.max_score
    pytest_weight = args.pytest_weight
    pylint_weight = args.pylint_weight
    scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)

    try:
        student_results = retrieve_student_results(student_dir)
    except:
        logger.error(f"Unable to find results file. Have you run the tests yet?")

    feedback_file_path = (student_dir / args.feedback_file).resolve()

    try:
        gen_feedback_file(student_results, feedback_file_path, scoring_params=scoring_params, force_feedback=args.force_feedback)
    except FileExistsError:
        print(f"{feedback_file_path} already exists and --force-feedback not specified")
    except:
        raise
