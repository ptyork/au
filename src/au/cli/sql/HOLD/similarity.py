#!/bin/env python3

import csv
import json
import os
import logging
import pprint
import difflib

from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

source = Path(os.path.abspath(os.getcwd()))
logging.debug(source)

assignment_name = source.name
logging.debug(assignment_name)

csv_filename = source.joinpath('grades.csv')
logging.debug(csv_filename)

###############################################################################
# LOAD ALL RAW FEEDBACK
###############################################################################

all_feedback = []

# Assume '{assignment_name}-' prefixes each assignment to grade
for subdir in source.iterdir():
    if not subdir.is_dir():
        logging.debug(f'SKIPPING: {subdir} (not dir)')
        continue
    pos = len(assignment_name) + 1
    
    student_name = subdir.name.split('@')[0]

    feedback_file = subdir / '.sanity-check' / 'raw-feedback.json'

    if feedback_file.exists():
        try:
            with open(feedback_file, 'rt') as fi:
                feedback = json.load(fi)
        except:
            logging.error(f'UNABLE TO PROCESS {feedback_file}')

        if len(feedback) == 0:
            logging.info(f'SKIPPING {student_name} (no feedback)')
            continue

        feedback = [q for q in feedback if q['issues'] and q['issues'][0] and q['issues'][0]['issue'] != 'empty']
        if len(feedback) == 0:
            logging.info(f'SKIPPING {student_name} (no queries)')
            continue

        logging.debug(f"found feedback for {student_name}")
        all_feedback.append({
            'student_name': student_name,
            'feedback': feedback
        })

    else:
        logging.info(f"SKIPPING {student_name} (no raw-feedback.json)")

###############################################################################
# FIND SIMILARITIES
###############################################################################

checked = []

for student in all_feedback:
    for other in all_feedback:
        if student == other or (other,student) in checked:
            continue

        stu_name = student['student_name']
        oth_name = other['student_name']

        logging.debug(f"{stu_name} vs. {oth_name}")

        checked.append((student,other))

        stu_queries = {q['query_name']:q for q in student['feedback']}
        other_queries = {q['query_name']:q for q in other['feedback']}

        common_queries = [key for key in stu_queries if key in other_queries]
        different_queries = [key for key in stu_queries if key not in other_queries]
        different_queries += [key for key in other_queries if key not in stu_queries]
        common_count = len(common_queries)
        different_count = len(different_queries)

        common_query_details = {}

        logging.debug(f"common_count = {common_count}")

        # only continue if 'similar enough'
        if common_count == 0 or common_count <= different_count:
            continue
        
        identical_count = 0
        total_items = 0
        total_diff = 0

        identical_line_count = 0
        total_line_count = 0

        for q,stu_fb in stu_queries.items():
            if q in other_queries:
                other_fb = other_queries[q]

                stu_items = stu_fb['issues']
                other_items = other_fb['issues']

                shared_items = [item for item in stu_items if item in other_items]
                diff = abs(len(stu_items) - len(shared_items))

                if diff == 0:
                    identical_count += 1

                stu_sql = stu_fb['sql'].replace("'","").replace('"','').splitlines()
                stu_sql = [line.strip() for line in stu_sql]
                other_sql = other_fb['sql'].replace("'","").replace('"','').splitlines()
                other_sql = [line.strip() for line in other_sql]

                total_line_count += len(stu_sql)
                line_diff = difflib.ndiff(stu_sql, other_sql)
                diff_string = ''
                for d in line_diff:
                    diff_string += d + '\n'
                    if d.startswith('  '):
                        identical_line_count += 1


                common_query_details[q] = {
                    'stu_items': stu_items,
                    'other_items': other_items,
                    'stu_sql': stu_fb['sql'],
                    'other_sql': other_fb['sql'],
                    'diff': diff_string
                }

            else:
                diff = len(stu_items)

            total_diff += diff
            total_items += len(stu_items)

        common_issue_pct = round(100 * (1 - ((total_diff * 1.0) / total_items)))
        common_sql_pct = round(100 * ((identical_line_count * 1.0) / total_line_count))

        logging.debug(f"common_issue_pct = {common_issue_pct}, common_sql_pct = {common_sql_pct}")

        if common_issue_pct > 90 and common_sql_pct > 70:
            logging.info(f'SIMILAR: {student["student_name"]} <> {other["student_name"]}')
            logging.info(f'         common issues:    {common_issue_pct}% from {common_count} queries')
            logging.info(f'         common sql:       {common_sql_pct}%')
            # pprint.pprint(common_queries)

            issue_file = source.joinpath(student['roster_name'] + '--' + other['roster_name'] + '.similarity.txt')
            logging.debug(f'Writing {issue_file}')
            try:
                with open(issue_file, "w") as fi:
                    fi.write(f'STUDENT 1:       {student["student_name"]}\n')
                    fi.write(f'STUDENT 2:       {other["student_name"]}\n')
                    fi.write(f'COMMON ISSUES:   {common_issue_pct}% from {common_count} queries\n')
                    fi.write(f'COMMON SQL:      {common_sql_pct}%\n')

                    for q, data in common_query_details.items():
                        fi.write('-'*80 + '\n')
                        fi.write(q + '\n')
                        fi.write('-'*80 + '\n')
                        fi.write(data['diff'] + '\n')

            except Exception as ex:
                logging.error(f"Error writing {issue_file}: {ex}")

