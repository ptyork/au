from typing import Dict
from dataclasses import dataclass

from au.lib.common.datetime_util import get_friendly_local_datetime
from au.lib.common.terminal_util import get_table, get_md_table_row

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


def get_student_scores(student_results: Dict, scoring_params: ScoringParams = ScoringParams()) -> Score:
    # Calculate score
    max = scoring_params.max_score
    pt_pct = student_results.setdefault('pytest_pct', 0)
    pt_weight = scoring_params.pytest_weight
    pl_pct = student_results.setdefault('pylint_pct', 0)
    pl_weight = scoring_params.pylint_weight
    total_score = round(max * ((pt_pct * pt_weight) + (pl_pct * pl_weight)), 2)

    return Score(pt_pct, pl_pct, total_score)


def get_summary(student_results: Dict, scoring_params: ScoringParams = None, get_markdown = False) -> str:
    summary_values = [
        ['Student Name', student_results['name'] ],
        ['Last Commit Date', get_friendly_local_datetime(student_results['commit_date'])],
        ['Last Commit Author', student_results['commiter_name']],
        ['Last Commit Message', student_results['commit_message']],
        ['Total Commit Count', student_results['num_commits']]
    ]
    if scoring_params:
        scores = get_student_scores(student_results, scoring_params)
        summary_values += [
            ['Funcationality Score', f"{scores.pytest_pct*100:.4g}% (weight: {scoring_params.pytest_weight*100:.4g}%)"],
            ['Code Style Score', f"{scores.pylint_pct*100:.4g}% (weight: {scoring_params.pylint_weight*100:.4g}%)"],
            ['Calculated Score', f"{scores.overall_score:g} / {scoring_params.max_score:g}"]
        ]
    else:
        summary_values += [
            ['Funcationality Score',f"{student_results['pytest_pct']*100:.4g}%"],
            ['Code Style Score', f"{student_results['pylint_pct']*100:.4g}%"]
        ]
    past_due = student_results.setdefault("past_due", None)
    if past_due:
        summary_values += [
            ['Past Due', past_due]
        ]
    return get_table(summary_values, col_widths=[25,52], get_markdown=get_markdown, lazy_end=True)

def get_summary_row(label: str, value: str):
    return get_md_table_row([label, value], col_widths=[25,52], lazy_end=True)