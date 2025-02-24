from typing import Dict
import click

import re
from pathlib import Path
from textwrap import wrap, indent
from pprint import pformat

from .eval_assignment import retrieve_student_results
from .scoring import get_summary, get_summary_row, get_student_scores, ScoringParams

import logging
_base_logging_level = logging.INFO
logging.basicConfig(level=_base_logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(_base_logging_level)

DEFAULT_FEEDBACK_FILE_NAME = 'FEEDBACK.md'

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


@click.command('gen-feedback')
@click.argument("student_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("--feedback-filename", type=str, default=DEFAULT_FEEDBACK_FILE_NAME,
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
def gen_feedback_cmd(student_dir: Path,
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

    try:
        student_results = retrieve_student_results(student_dir)
    except:
        logger.error(f"Unable to find results file. Have you run the tests yet?")
    
    scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)
    gen_feedback(student_results, student_dir, feedback_filename, scoring_params, overwrite_feedback)
    

def gen_feedback(student_results: Dict[str,any],
                 student_dir: Path,
                 feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
                 scoring_params: ScoringParams = ScoringParams(),
                 overwrite_feedback = False) -> None:
    '''
    Generate a feedback file for a single student
    '''

    feedback_file_path = (student_dir / feedback_filename).resolve()

    if feedback_file_path.exists() and not overwrite_feedback:
        logger.info(f"SKIPPING: {feedback_file_path} already exists and --overwrite-feedback not specified")

    summary = get_summary(student_results, scoring_params, get_markdown=True)
    scores = get_student_scores(student_results, scoring_params)
    final_score_row = get_summary_row("Final Score", f"{scores.overall_score:g}")


    with open(feedback_file_path, 'w') as fi:
        def wl(txt = ''):
            fi.write(str(txt) + '\n')

        regex_clean = re.compile(r'.+Error:.+?\s:', re.DOTALL)
        def print_pytest(test):
            if not test.get('status') == 'pass':
                name = test.get('name', 'Unnamed Test')
                parent_test_class = test.get('parent_test_class')
                parent_test_name = test.get('parent_test_name')
                test_name = parent_test_class
                if parent_test_name:
                    test_name += " >> " + parent_test_name
                test_name += " >> " + name
                message = test.get('message', 'No message provided')
                message = regex_clean.sub('', message).strip()
                wl(f"{test_name}")
                wl(indent(message, '    '))
                wl()
                wl(' •' * 20)
                wl()


        wl('# Assignment Feedback')
        wl()
        wl(summary)
        wl(final_score_row)
        wl()
        wl()
        wl('-'*80)
        wl('## Grader Comments:')
        wl()
        wl()
        wl()

        pytest_results = student_results.get('pytest_results')
        if pytest_results:
            logger.debug('pytest_results: ' + pformat(pytest_results))
            wl()
            wl('-'*80)
            wl('## Functionality Feedback (pytest)')
            wl('-'*80)
            wl('```')
            test: Dict
            test_classes = pytest_results.get('test_classes')
            if test_classes:
                for test_class in test_classes.values():
                    if test_class.get('status') == 'pass':
                        continue
                    tests = test_class.get('tests')
                    if tests:
                        for test in tests.values():
                            if test.get('status') == 'pass':
                                continue
                            sub_tests = test.get('sub_tests')
                            if sub_tests:
                                for sub_test in sub_tests:
                                    if sub_test.get('status') == 'pass':
                                        continue
                                    print_pytest(sub_test)
                            else:
                                print_pytest(test)
            wl("```")

        pylint_results = student_results.get('pylint_results')
        if pylint_results:
            logger.debug('pylint_results: ' + pformat(pylint_results))
            wl()
            wl('-'*80)
            wl('## Code Style Feedback (pylint)')
            wl()
            wl('```')
            messages = pylint_results.get('messages', [])
            msg: Dict
            for msg in messages:
                path = msg.get('path', 'General Message')
                line = msg.get('line', 0)
                line_str = f" line: {line}" if line else ""
                col = msg.get('col', 0)
                col_str = f" col: {col}" if col else ""
                id = msg.get('messageId', "No ID")
                msg_type = msg.get('type', '')
                message = msg.get('message', "No message provided")
                wl(f"{msg_type}: {path}{line_str}{col_str} ({id}):")
                wl('\n'.join(wrap(message, 80, initial_indent="    ", subsequent_indent="    ")))
                wl()
                wl(' •' * 20)
                wl()

            # wl(pformat(student_results['pylint_results']))
            wl('```')


if __name__ == "__main__":
    gen_feedback_cmd()
