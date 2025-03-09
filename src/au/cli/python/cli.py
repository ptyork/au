import click

from au.click import AliasedGroup

from .eval_assignment import eval_assignment_cmd
from .gen_feedback import gen_feedback_cmd
from .gen_grades_csv import gen_grades_csv_cmd
from .quick_grade import quick_grade


@click.group(cls=AliasedGroup)
def python():
    """Commands for working with Python assignments."""


python.add_command(eval_assignment_cmd)
python.add_command(gen_feedback_cmd)
python.add_command(gen_grades_csv_cmd)
python.add_command(quick_grade)


if __name__ == "__main__":
    python()
