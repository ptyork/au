import logging
from pathlib import Path
import csv

import click

from au.click import BasePath, DebugOptions
from au.common.datetime import get_friendly_local_datetime

from .gen_feedback import get_feedback_file_score, DEFAULT_FEEDBACK_FILE_NAME
from .eval_assignment import retrieve_student_results


logger = logging.getLogger(__name__)


DEFAULT_GRADES_FILE_NAME = "grades.csv"


@click.command("gen-grades-csv")
@click.argument("root_dir", type=BasePath(), default=".")
@click.option(
    "--feedback-filename",
    type=str,
    default=DEFAULT_FEEDBACK_FILE_NAME,
    help="name of markdown file to generate",
)
@click.option(
    "--grades-filename",
    type=str,
    default=DEFAULT_GRADES_FILE_NAME,
    help="name of CSV file containing student feedback",
)
@click.option(
    "-y",
    "--skip-confirm",
    is_flag=True,
    help="set to bypass confirmation and overwrite existing CSV",
)
@DebugOptions().options
def gen_grades_csv_cmd(
    root_dir: Path,
    grades_filename: str = DEFAULT_GRADES_FILE_NAME,
    feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
    skip_confirm: bool = False,
    **kwargs,
) -> None:
    """Generate grades CSV file from feedback files in ROOT_DIR."""
    gen_grades_csv(root_dir, grades_filename, feedback_filename, skip_confirm)


def gen_grades_csv(
    root_dir: Path,
    grades_filename: str = DEFAULT_GRADES_FILE_NAME,
    feedback_filename: str = DEFAULT_FEEDBACK_FILE_NAME,
    skip_confirm: bool = False,
) -> None:
    """Generate grades CSV file from feedback files in ROOT_DIR."""

    grades_file = root_dir / grades_filename

    if not skip_confirm and grades_file.exists():
        click.confirm(f"Overwrite {grades_file}", abort=True)

    csv_header = [
        "Name",
        "Score",
        "Past Due",
        "Commit Count",
        "Last Commit",
        "Directory",
    ]
    csv_rows = []

    dirs = list(root_dir.iterdir())
    dirs.sort()

    for student_dir in dirs:
        if not student_dir.is_dir():
            continue

        try:
            student_results = retrieve_student_results(student_dir)
        except:
            logger.warning(f"No evaluation results found in {student_dir.name}")
            continue

        feedback_file = student_dir / feedback_filename
        if not feedback_file.exists():
            logger.warning(f"{feedback_filename} not found in {student_dir.name}")
            continue

        try:
            score = get_feedback_file_score(feedback_file)
        except:
            logger.error(f"Error retrieving score from {student_dir.name}")
            continue

        row = [student_results["name"], score]
        pd = student_results.setdefault("past_due", None)
        if pd:
            row.append(pd)
        else:
            row.append("")
        num_commits = student_results["num_commits"]
        row.append(num_commits)
        if num_commits:
            row.append(
                get_friendly_local_datetime(student_results["commit_date"]),
            )
        else:
            row.append("")
        row.append(student_results["dir_name"])

        csv_rows.append(row)

    with open(grades_file, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_header)
        writer.writerows(csv_rows)

    print(f"Processed {len(csv_rows)} student grades")
    print(f"Generated {grades_filename} in {root_dir}")


if __name__ == "__main__":
    gen_grades_csv_cmd()
