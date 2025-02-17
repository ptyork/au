#!/usr/bin/env python3

import logging
import csv
import os
from pathlib import Path
from datetime_util import get_friendly_local_datetime
from gh_gen_feedback import get_feedback_file_score
from gh_run_tests import retrieve_student_results


logger = logging.getLogger(__name__)


def gen_grades_csv(root_dir: Path, csv_filename: str = 'grades.csv', feedback_filename: str = 'FEEDBACK.md'):

    csv_header = [
        "Name", "Score", "Past Due", "Commit Count", "Last Commit",  "Directory"
    ]
    csv_rows = []

    dirs = list(root_dir.iterdir())
    dirs.sort()

    for student_dir in dirs:
        if not student_dir.is_dir():
            continue

        feedback_file = student_dir / feedback_filename
        if not feedback_file.exists():
            continue
        
        score = get_feedback_file_score(feedback_file)

        student_results = retrieve_student_results(student_dir)

        row = [
            student_results["name"],
            score
        ]
        pd = student_results.setdefault('past_due', None)
        if pd:
            row.append(pd)
        else:
            row.append('')
        num_commits = student_results['num_commits']
        row.append(num_commits)
        if num_commits:
            row.append(get_friendly_local_datetime(student_results['commit_date']),)
        else:
            row.append('')
        row.append(student_results['dir_name'])

        csv_rows.append(row)

    with open(root_dir / csv_filename, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_header)
        writer.writerows(csv_rows)


if __name__ == "__main__":

    import argparse

    _base_logging_level = logging.WARNING

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(_base_logging_level)


    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.description = '''
    '''

    parser.add_argument("root_dir", type=str, help="the directory containing the student repositories")
    parser.add_argument("--grades-csv", help="name of the CSV file that will store the grades (default=`grades.csv`)", type=str, default='grades.csv')
    parser.add_argument("--feedback-file", help="name of markdown files that contains feedback (default=`FEEDBACK.md`)", type=str, default='FEEDBACK.md')
    parser.add_argument("-y", "--skip-confirm", help="set to skip confirmation to overwrite grades.csv", action="store_true")
    parser.add_argument("-d", "--debug", help="set to enable detailed output", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    root_dir = Path(os.path.abspath(args.root_dir))

    if not root_dir.is_dir():
        logger.error(f"{root_dir} is not a valid directory")
        exit(1)

    csv_file = root_dir / args.grades_csv
    if not args.skip_confirm and csv_file.exists():
        while True:
            resp = input(f"Overwrite {csv_file} (Y/n)? ").lower()
            if resp == 'n':
                exit(0)
            if resp == '' or resp == 'y':
                break

    gen_grades_csv(root_dir, args.grades_csv, args.feedback_file)
