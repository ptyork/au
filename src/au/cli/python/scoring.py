from dataclasses import dataclass

from craftable import get_table, get_table_row
from craftable.styles import MarkdownStyle, NoBorderScreenStyle

from au.common.datetime import get_friendly_local_datetime

from .pytest_data import Results
from .types import StudentResults


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
    student_results: StudentResults, scoring_params: ScoringParams = ScoringParams()
) -> Score:
    # Calculate score (fallback to pt_pct if no test_classes)
    pt_pct = student_results.setdefault("pytest_pct", 0)
    pl_pct = student_results.setdefault("pylint_pct", 0)

    test_classes = []
    try:
        pytest_results = Results.from_dict(student_results.get("pytest_results"))
        test_classes = pytest_results.test_classes.values()
    except:
        pass

    if test_classes:
        tests_count = 0
        correct_count = 0
        for test_class in test_classes:
            tests_count += len(test_class.tests)
            correct_count += test_class.pass_count
        if tests_count > 0:
            pt_pct = correct_count / tests_count

    total_score = None
    if scoring_params:
        max = scoring_params.max_score
        pt_weight = scoring_params.pytest_weight
        pl_weight = scoring_params.pylint_weight
        total_score = round(max * ((pt_pct * pt_weight) + (pl_pct * pl_weight)), 2)

    return Score(pt_pct, pl_pct, total_score)


def get_summary(
    student_results: StudentResults, scoring_params: ScoringParams = None, get_markdown=False
) -> str:
    summary_values = [["Student Name", student_results["name"]]]

    if "commit_date" in student_results:
        summary_values.extend(
            [
                [
                    "Last Commit Date",
                    get_friendly_local_datetime(student_results["commit_date"]),
                ],
                ["Last Commit Author", student_results["commiter_name"]],
                ["Last Commit Message", student_results["commit_message"]],
                ["Total Commit Count", student_results["num_commits"]],
            ]
        )

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

    test_classes = []
    try:
        pytest_results = Results.from_dict(student_results.get("pytest_results"))
        test_classes = pytest_results.test_classes.values()
    except:
        pass

    if test_classes:
        summary_values.append(
            ["Functionality Score", f"{scores.pytest_pct*100:.4g}% {pytest_weight}"],
        )
        for test_class in test_classes:
            tot = len(test_class.tests)
            correct = test_class.pass_count
            summary_values.append([f" + {test_class.name}", f"{correct} out of {tot}"])
    else:
        summary_values.append(["Functionality Score", "N/A"])

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
