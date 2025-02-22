import click
from yaspin import yaspin

from au.lib.click.AliasedGroup import AliasedGroup

@click.group(cls=AliasedGroup)
def python():
    """Commands for working with Python assignments."""
    pass

from .eval_assignment import eval_assignment_cmd
python.add_command(eval_assignment_cmd)

from .gen_feedback import gen_feedback_cmd
python.add_command(gen_feedback_cmd)

from .gen_grades_csv import gen_grades_csv_cmd
python.add_command(gen_grades_csv_cmd)

from .quick_grade import quick_grade
python.add_command(quick_grade)

# @python.command()
# @click.argument("path", required=False, type=click.Path(resolve_path=True))
# def do_something(path):
#     print(f"RUH TEST COMMAND: {path}")


if __name__ == "__main__":
    python()
