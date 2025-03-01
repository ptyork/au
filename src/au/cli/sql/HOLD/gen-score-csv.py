#!/usr/bin/python3

import csv
import os
import logging
import pprint

from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

source = Path(os.path.abspath(os.getcwd()))
logging.debug(source)

assignment_name = source.name
logging.debug(assignment_name)

csv_filename = source / 'grades.csv'
logging.debug(csv_filename)

scores = []
score_prefix = '## SCORE:'

###############################################################################
# FIND ALL ASSIGNMENTS
###############################################################################

assignments = []

# Assume '{assignment_name}-' prefixes each assignment to grade
for subdir in source.iterdir():
    if not subdir.is_dir():
        logging.debug(f'SKIPPING: {subdir} (not dir)')
        continue
    feedback_file = subdir / 'FEEDBACK.md'
    if not feedback_file.exists():
        logging.info(f'SKIPPING: {subdir} (no feedback)')
        continue
    
    student_name = subdir.name.split('@')[0]

    logging.debug(f"found feedback for {student_name}")

    ###############################################################################
    # EXTRACT ALL SCORES
    ###############################################################################

    score = ''

    try:
        with open(feedback_file, 'rt') as fi:
            for line in fi:
                if line.startswith(score_prefix):
                    score = line.replace(score_prefix, '').strip()
                    logging.info(f'SCORE for {student_name}: {score}')
                    break
    except:
        logging.error(f'UNABLE TO PROCESS {feedback_file}')
    if not score:
        logging.info(f'SKIPPING {student_name} (no score)')

    scores.append([student_name, score])

scores.sort()

logging.debug(pprint.pformat(scores, indent=4))

###############################################################################
# WRITE CSV
###############################################################################

try:
    with open(csv_filename, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(('student','score'))
        writer.writerows(scores)
except Exception as ex:
    logging.error(f"Error reading {csv_filename}: {ex}")
