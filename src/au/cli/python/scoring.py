from typing import Dict
from dataclasses import dataclass

from f_table import MarkdownStyle, NoBorderScreenStyle, get_table, get_table_row

from au.common.datetime import get_friendly_local_datetime

from .pytest_data import Results


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


def get_student_scores(
    student_results: Dict, scoring_params: ScoringParams = ScoringParams()
) -> Score:
    # Calculate score
    pt_pct = student_results.setdefault("pytest_pct", 0)
    pl_pct = student_results.setdefault("pylint_pct", 0)
    total_score = None
    if scoring_params:
        max = scoring_params.max_score
        pt_weight = scoring_params.pytest_weight
        pl_weight = scoring_params.pylint_weight
        total_score = round(max * ((pt_pct * pt_weight) + (pl_pct * pl_weight)), 2)

    return Score(pt_pct, pl_pct, total_score)


def get_summary(
    student_results: Dict, scoring_params: ScoringParams = None, get_markdown=False
) -> str:
    summary_values = [
        ["Student Name", student_results["name"]],
        [
            "Last Commit Date",
            get_friendly_local_datetime(student_results["commit_date"]),
        ],
        ["Last Commit Author", student_results["commiter_name"]],
        ["Last Commit Message", student_results["commit_message"]],
        ["Total Commit Count", student_results["num_commits"]],
    ]

    pytest_weight = ""
    pylint_weight = ""
    final_score_row = None
    if scoring_params:
        pytest_weight = f"(weight: {scoring_params.pytest_weight*100:.4g}%)"
        pylint_weight = f"(weight: {scoring_params.pylint_weight*100:.4g}%)"
        scores = get_student_scores(student_results, scoring_params)
        final_score_row = [
            "Calculated Score",
            f"{scores.overall_score:g} / {scoring_params.max_score:g}",
        ]
    else:
        scores = get_student_scores(student_results, None)

    summary_values.append(
        ["Functionality Score", f"{scores.pytest_pct*100:.4g}% {pytest_weight}"],
    )

    try:
        pytest_results = Results.from_dict(student_results.get("pytest_results"))
        for test_class in pytest_results.test_classes.values():
            tot = len(test_class.tests)
            correct = test_class.pass_count
            summary_values.append([f" + {test_class.name}", f"{correct} out of {tot}"])
    except:
        pass

    summary_values.append(
        ["Code Style Score", f"{scores.pylint_pct*100:.4g}% {pylint_weight}"],
    )

    if final_score_row:
        summary_values.append(final_score_row)

    past_due = student_results.setdefault("past_due", None)
    if past_due:
        summary_values.append(["Past Due", past_due])

    style = MarkdownStyle() if get_markdown else NoBorderScreenStyle()
    return get_table(summary_values, col_defs=["25T", "52"], lazy_end=True, style=style)


def get_summary_row(label: str, value: str):
    return get_table_row(
        [label, value], col_defs=["25T", "52"], lazy_end=True, style=MarkdownStyle()
    )
