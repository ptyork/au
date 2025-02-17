#!/usr/bin/env python3
from typing import Dict

import click

import json
import os
import sys
from io import StringIO
from pathlib import Path
from datetime import datetime, date, timezone
from git import Repo, Commit
import pytest
import pylint.lint as lint
from pylint.reporters.json_reporter import JSON2Reporter
from yaspin import yaspin

from .pytest_reporter import PytestResultsReporter
from .scoring import get_summary

from au.lib.common.terminal_util import draw_single_line
from au.lib.github.classroom_types import Classroom, Assignment
from au.lib.github.classroom_util import choose_classroom, get_assignment, choose_assignment
from au.lib.common.datetime_util import get_friendly_timedelta

import logging
_base_logging_level = logging.INFO
logging.basicConfig(level=_base_logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(_base_logging_level)

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


@click.command('eval-assignment')
@click.argument("student_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("-s", "--student-name", type=str,
              help="the name of the student for the feedback report; will default to the GitHub username if not provided")
@click.option("-a", "--assignment-id", type=int,
              help="the integer classroom id for the assignment; will prompt for the classroom and assignment if not provided")
@click.option("-n", "--no-summary", is_flag=True, help="set to not display any summary tables")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
def eval_assignment_cmd(student_dir: Path,
                        student_name: str = None,
                        assignment_id: int = None,
                        no_summary: bool = False,
                        debug: bool = False,
                        quiet: bool = False) -> None:
    '''
    Run automated grading tests on a single student directory
    '''

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if assignment_id:
        assignment = get_assignment(assignment_id)
    else:
        classroom: Classroom = choose_classroom()
        assignment: Assignment = choose_assignment(classroom)

    if not assignment:
        logger.warning("Unable to find the requested assignment. Functionality will be limited.")

    if assignment and not no_summary:
        print(assignment)

    student_results = eval_assignment(student_dir, student_name, assignment)

    if student_results and not no_summary:
        draw_single_line(f'Summary Results')
        print(get_summary(student_results))


def eval_assignment(student_dir: Path,
                    student_name: str = None,
                    assignment: Assignment = None) -> Dict[str, any]:
    '''
    Run automated grading tests on a single student directory
    '''
    
    dir_name = student_dir.name

    os.chdir(student_dir)

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

    draw_single_line('pytest')

    try:
        # run the tests and report
        pytest_reporter = PytestResultsReporter()
        keep_packages = ['_asyncio',
                         '_contextvars',
                         '_elementtree',
                         '_pytest',
                         '_ssl',
                         'asyncio',
                         'attr',
                         'cmd',
                         'code',
                         'codeop',
                         'contextvars',
                         'faulthandler',
                         'pdb',
                         'pkgutil',
                         'pyexpat',
                         'pytest_metadata',
                         'pytest_subtests',
                         'readline',
                         'ssl',
                         'unittest',
                         'xml']

        pretest_modules = [key for key in sys.modules.keys()]
        
        pytest.main(
            # ['-s', '--tb=no', '-q','--import-mode=importlib'],
            # ['-s', '--tb=no', '-q','--import-mode=append'],
            # ['-s', '--tb=no', '-q','--import-mode=prepend','--cache-clear','--rootdir='+str(student_dir)],
            # ['-s', '--tb=no', '-q'],
            ['--tb=no', '-q'],
            plugins=[pytest_reporter]
        )

        posttest_modules = [key for key in sys.modules.keys()]
        for module_name in posttest_modules:
            if module_name in pretest_modules:
                continue
            package = module_name.split('.')[0]
            if package in keep_packages:
                continue
            del sys.modules[module_name]

        pytest_pct = round(pytest_reporter.results.pass_pct, 3)
        student_results['pytest_pct'] = pytest_pct
        if pytest_pct < 1:
            student_results['pytest_results'] = pytest_reporter.results.as_dict()

    except Exception as ex:
        print("EXCEPTION:", ex)
        student_results['pytest_exception'] = ex

    print("done with pytest")
    
    ###############################################################################
    # PYLINT
    ###############################################################################

    draw_single_line('pylint')

    lint_files = []
    for root, dirs, files in os.walk(student_dir):
        dirs[:] = [d for d in dirs if d[0] != '.' and d != "test" and d != "tests"]
        rel_root = Path(root).relative_to(student_dir)

        for file in files:
            if (
                file.endswith('.py') and
                not file.startswith('.') and
                not file.startswith('test_') and
                not file.endswith('_test.py')
            ):
                lint_files.append(str(student_dir / rel_root / file))

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
            'W0702',
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

        with yaspin(text=f"Running pylint...please wait...").aesthetic as sp:
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
    eval_assignment_cmd()
