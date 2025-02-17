import click
from yaspin import yaspin

from au.lib.click.AliasedGroup import AliasedGroup

@click.group("python", short_help="Commands for working with Python assignments.", cls=AliasedGroup)
def main():
    pass

from .eval_assignment import eval_assignment_cmd
main.add_command(eval_assignment_cmd)

from .gen_feedback import gen_feedback_cmd
main.add_command(gen_feedback_cmd)

from .quick_grade import quick_grade
main.add_command(quick_grade)

from .gen_grades_csv import gen_grades_csv_cmd
main.add_command(gen_grades_csv_cmd)


# @main.command()
# @click.argument("path", required=False, type=click.Path(resolve_path=True))
# def do_something(path):
#     print(f"RUH TEST COMMAND: {path}")
