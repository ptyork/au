#!/usr/bin/env python3

from typing import Dict

import json
import logging
import os
from io import StringIO
from pathlib import Path
from datetime import datetime, date, timezone

from git import Repo, Commit

import pytest
import pylint.lint as lint
from pylint.reporters.json_reporter import JSON2Reporter

from pytest_reporter import PytestResultsReporter
from terminal_util import draw_single_line, draw_double_line
from gh_classroom_types import Course, Assignment
from gh_classroom_util import get_course, get_assignment, choose_assignment
from datetime_util import get_friendly_timedelta

logger = logging.getLogger(__name__)


RESULTS_FILE_NAME = '.test_results.json'

def _json_deserialize_hook(dct: Dict):
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                dct[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                pass
    return dct

def retrieve_student_results(student_dir: Path) -> Dict:
    results_file = student_dir / RESULTS_FILE_NAME
    with open(results_file, 'r') as fi:
        return json.load(fi, object_hook=_json_deserialize_hook)

def run_tests(student_dir_path: Path, assignment: Assignment = None, student_name: str = None) -> Dict:
    
    dir_name = str(student_dir_path).split(os.sep)[-1]

    os.chdir(student_dir_path)

    student_results: dict = {}

    student_results['name'] = student_name
    student_results['dir_name'] = dir_name
    if assignment:
        student_results['assignment_title'] = assignment.title
        student_results['assignment_deadline'] =  assignment.deadline

    ###############################################################################
    # REPO CHECKS
    ###############################################################################

    try:
        repo = Repo()
        assert(repo)
    except:
        logger.error(f"No git repository found in {dir_name}")
        return None

    commits: list[Commit]  = []
    for last_commit in repo.iter_commits():
        if "[bot]" in last_commit.author.name:
            break
        commits.append(last_commit)

    student_results["num_commits"] = len(commits)
    if commits:
        last_commit = commits[0]
        if not student_name:
            student_results['name'] = last_commit.author.name
        student_results["commit_message"] = last_commit.message.strip()
        student_results["commiter_name"] = last_commit.author.name
        commit_date = datetime.fromtimestamp(last_commit.committed_date, timezone.utc)
        student_results["commit_date"] = commit_date
        if assignment:
            past_due = commit_date - assignment.deadline
            if past_due.total_seconds() > 0:
                student_results["past_due"] = get_friendly_timedelta(past_due)
    else:
        print(f"SKIPPING {student_results['name']}...no commits")
        return None

    ###############################################################################
    # PYTEST
    ###############################################################################

    draw_single_line('Running pytest')

    try:
        # run the tests and report
        pytest_reporter = PytestResultsReporter()
        pytest.main(
            ['-s', '--tb=no', '-q','--import-mode=importlib'],
            plugins=[pytest_reporter]
        )
        
        pytest_pct = round(pytest_reporter.results.pass_pct, 3)
        student_results['pytest_pct'] = pytest_pct
        if pytest_pct < 1:
            student_results['pytest_results'] = pytest_reporter.results.as_dict()

    except Exception as ex:
        student_results['pytest_exception'] = ex

    print("done with pytest")
    
    ###############################################################################
    # PYLINT
    ###############################################################################

    draw_single_line('Running pylint')

    lint_files = []
    for root, dirs, files in os.walk(student_dir_path):
        dirs[:] = [d for d in dirs if d[0] != '.' and d != "test" and d != "tests"]
        rel_root = Path(root).relative_to(student_dir_path)

        for file in files:
            if (
                file.endswith('.py') and
                not file.startswith('.') and
                not file.startswith('test_') and
                not file.endswith('_test.py')
            ):
                lint_files.append(str(student_dir_path / rel_root / file))

    if lint_files:
        lint_disabled = [
            'C0103',
            'C0114',
            'C0115',
            'C0116',
            'C0303',
            'C0304',
            'C0305',
            'R0801',
            'R0903',
            'R0913',
            'R0914',
            'R0915',
            'W1309',
            'R1716',
            'R1722'
        ]
        lint_args = []
        lint_args += ['--disable=' + ','.join(lint_disabled)]
        # lint_args += ['--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}']
        lint_args += lint_files
        pylint_output = StringIO()  # Custom open stream
        pylint_reporter = JSON2Reporter(pylint_output)
        # pylint_reporter = TextReporter(pylint_output)

        try:
            lint.Run(lint_args, reporter=pylint_reporter, exit=False)
            pylint_results = json.loads(pylint_output.getvalue())
            pylint_pct = round(pylint_results['statistics']['score'] / 10.0, 3)
            student_results['pylint_pct'] = pylint_pct
            if pylint_pct < 1:
                student_results['pylint_results'] = pylint_results
        except Exception as ex:
            student_results['pylint_exception'] = ex
            print(ex)
    else:
        logger.error('No files found to lint found')

    print("done with pylint")

    ###############################################################################
    # Save and return the test results data
    ###############################################################################

    def _json_serialize(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

    with open(RESULTS_FILE_NAME, 'w') as fi:
        json.dump(student_results, fi, indent=2, default=_json_serialize)

    return student_results



if __name__ == "__main__":
    
    import argparse
    from gh_classroom_util import print_course, print_assignment

    _base_logging_level = logging.WARNING

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(_base_logging_level)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.description = '''
    '''

    parser.add_argument("student_dir", type=str, help="the directory containing the student repository")
    parser.add_argument("-s", "--student-name", help="the name of the student for the feedback report; will default to the GitHub username if not provided", type=str, default=None)
    parser.add_argument("-a", "--assignment-id", help="the integer course id for the assignment; will prompt for the course and assignment if not provided", type=int, default=None)
    parser.add_argument("-d", "--debug", help="set to enable detailed output", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    student_dir = Path(os.path.abspath(args.student_dir))

    if not student_dir.is_dir():
        logger.error(f"{student_dir} is not a valid directory")
        exit(1)

    if args.assignment_id:
        course, assignment = get_assignment(args.assignment_id)
    else:
        course: Course = get_course()
        if course:
            assignment: Assignment = choose_assignment(course)

    if assignment:
        print_course(course)
        print_assignment(assignment)
    else:
        logger.error("Unable to find the requested assignment. Functionality will be limited.")


    run_tests(student_dir, assignment, args.student_name)
