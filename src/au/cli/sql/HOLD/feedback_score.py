#!/usr/bin/python3

# GENERATE FEEDBACK SCORE
# 
#   This parses FEEDBACK.md for deductions. It sums these deductions and applies
#   a final score to the file.

import logging
import props
from os import getcwd
from os.path import isfile

logging.basicConfig(level=logging.INFO)

if not isfile(props.FEEDBACK_FILENAME):
    logging.info(f"skipping {getcwd()} because {props.FEEDBACK_FILENAME} doesn't exist")
    exit(0)

logging.info(f"processing {getcwd()}...")

deduction_const = '(DEDUCTION:'
total_deductions = 0.0
deduction_count = 0
nonempty_deductions = 0

with open(props.FEEDBACK_FILENAME, 'r') as fi:
    feedback_lines = fi.readlines()

for line in feedback_lines:
    line = line.strip()

    if deduction_const in line:
        deduction_count += 1

        idx = line.index(deduction_const) + len(deduction_const)

        ded_str = ''
        for c in line[idx:]:
            if c == '.' or c.isdigit():
                ded_str += c
            elif c == ')':
                break

        if not ded_str:
            continue

        try:
            ded = float(ded_str)
            total_deductions += ded
            nonempty_deductions += 1
        except:
            print(f"Unable to parse deduction for '{line}'")
            continue

score = max( 100 - total_deductions, 0 ) # 0 is the lowest score possible

logging.debug(f"{deduction_count} deductions found")
logging.debug(f"{nonempty_deductions} non-zero deductions found")
logging.debug(f"{total_deductions} total deductions")

if deduction_count == nonempty_deductions:
    logging.info(f"SCORE: {score}")

    score_prefix = '## SCORE: '
    score_line = f'{score_prefix}{score:g}\n'
    if feedback_lines[1].startswith(score_prefix):
        feedback_lines[1] = score_line
    else:
        feedback_lines.insert(1, score_line)

    with open(props.FEEDBACK_FILENAME, 'w') as fi:
        fi.writelines(feedback_lines)

else:
    logging.info(f"SKIPPING DUE TO EMPTY SCORES")