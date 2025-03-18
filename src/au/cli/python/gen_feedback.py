from typing import Dict
import logging
import re
from pathlib import Path
from textwrap import wrap, indent
from pprint import pformat

import click

from au.click import BasePath, DebugOptions

from .eval_assignment import retrieve_student_results
from .pytest_data import Results, Test, SubTest
from .scoring import get_summary, get_summary_row, get_student_scores, ScoringParams


logger = logging.getLogger(__name__)


DEFAULT_FEEDBACK_FILE_NAME = "FEEDBACK.md"


def get_feedback_file_score(feedback_file_path: Path) -> str:
    """
    Returns score as string in case it has been annotated in the feedback file.
    """
    score = None
    with open(feedback_file_path, "r") as fi:
        for line in fi:
            if line.startswith("| Final Score"):
                parts = line[2:].split("|")
                score = parts[1].strip()
                break
    return score


@click.command("gen-feedback")
@click.argument("student_dir", type=BasePath(), required=True)
@click.option(
    "--feedback-filename",
    type=str,
    default=DEFAULT_FEEDBACK_FILE_NAME,
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
def gen_feedback_cmd(
    student_dir: Path,
    feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
    overwrite_feedback: bool = False,
    max_score: int = 10,
    pytest_weight: float = 1.0,
    pylint_weight: float = 0.0,
    **kwargs,
) -> None:
    """Generate a feedback file for a single assignment."""
    logging.basicConfig()

    try:
        student_results = retrieve_student_results(student_dir)
    except:
        logger.error(f"Unable to find results file. Have you run the tests yet?")

    #################################################################
    # TODO: Pull feedback filename and scoring params from settings

    scoring_params = ScoringParams(max_score, pytest_weight, pylint_weight)
    gen_feedback(
        student_results,
        student_dir,
        feedback_filename,
        scoring_params,
        overwrite_feedback,
    )


def gen_feedback(
    student_results: Dict[str, any],
    student_dir: Path,
    feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
    scoring_params: ScoringParams = ScoringParams(),
    overwrite_feedback=False,
) -> None:
    """Generate a feedback file for a single student."""
    feedback_file_path = (student_dir / feedback_filename).resolve()

    if feedback_file_path.exists() and not overwrite_feedback:
        logger.info(
            f"SKIPPING: {feedback_file_path} already exists and --overwrite-feedback not specified"
        )
        return

    summary = get_summary(student_results, scoring_params, get_markdown=True)
    scores = get_student_scores(student_results, scoring_params)
    final_score_row = get_summary_row("Final Score", f"{scores.overall_score:g}")

    with open(feedback_file_path, "w") as fi:

        def wl(txt=""):
            fi.write(str(txt) + "\n")

        regex_clean = re.compile(r".+Error:.+?\s:", re.DOTALL)

        def print_test(test: Test | SubTest):
            if not test.is_passing():
                full_name = test.parent_test_class
                if isinstance(test, SubTest):
                    full_name += " >> " + test.parent_test_name
                full_name += " >> " + (test.name if test.name else "Unnamed Test")
                message = regex_clean.sub("", test.message).strip()
                wl(f"{full_name}")
                wl(indent(message, "    "))
                wl()
                wl(" •" * 20)
                wl()

        wl("# Assignment Feedback")
        wl()
        wl(summary)
        wl(final_score_row)
        wl()
        wl()
        wl("-" * 80)
        wl("## Grader Comments:")
        wl()
        wl()
        wl()

        pytest_results_d = student_results.get("pytest_results")
        if pytest_results_d:
            logger.debug("pytest_results: " + pformat(pytest_results_d))
            pytest_results = Results.from_dict(pytest_results_d)
            if pytest_results.pass_pct < 1:
                wl()
                wl("-" * 80)
                wl("## Functionality Feedback (pytest)")
                wl()
                wl("```")
                for test_class in pytest_results.test_classes.values():
                    if test_class.is_passing():
                        continue
                    for test in test_class.tests.values():
                        if test.is_passing():
                            continue
                        if test.sub_tests:
                            for sub_test in test.sub_tests:
                                if sub_test.get("status") == "pass":
                                    continue
                                print_test(sub_test)
                        else:
                            print_test(test)
                wl("```")

        pylint_results = student_results.get("pylint_results")
        if pylint_results:
            logger.debug("pylint_results: " + pformat(pylint_results))
            wl()
            wl("-" * 80)
            wl("## Code Style Feedback (pylint)")
            wl()
            wl("```")
            messages = pylint_results.get("messages", [])
            msg: Dict
            for msg in messages:
                path = msg.get("path", "General Message")
                line = msg.get("line", 0)
                line_str = f" line: {line}" if line else ""
                col = msg.get("col", 0)
                col_str = f" col: {col}" if col else ""
                id = msg.get("messageId", "No ID")
                msg_type = msg.get("type", "")
                message = msg.get("message", "No message provided")
                wl(f"{msg_type}: {path}{line_str}{col_str} ({id}):")
                wl(
                    "\n".join(
                        wrap(
                            message, 80, initial_indent="    ", subsequent_indent="    "
                        )
                    )
                )
                wl()
                wl(" •" * 20)
                wl()

            # wl(pformat(student_results['pylint_results']))
            wl("```")


if __name__ == "__main__":
    gen_feedback_cmd()
