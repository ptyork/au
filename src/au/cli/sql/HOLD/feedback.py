#!/usr/bin/python3

# GENERATE FEEDBACK
# 
#     This script generates a FEEDBACK.md file that contains results of the
#     full suite of automated tests run against all sql files in this
#     fullcheck.json file.
# 
#     TODO:
#       * Add UsesDistinct
#         - And catch DISTINCT(...)
#       * Add UsesLimit
#       * Add UsesLike (or REGEXP)
#       * Add UsesOuterJoin
#       * Add basic style checks / linting
#       * DONE Support multi-line/fully-delimited comments /* ... */
#       * ORDER BY "stringLiteral"
#       * Add explicit support for ORDER BY
#       * Suppress "expect to find value" feedback for missing cols
#       

from commonutil import ps, wb, fullpath
from commonsql import resetDatabase, parseSQL, getProperties
import props
import json
from os import getcwd
from os.path import isfile
from pathlib import(Path)
import re
from pprint import pformat
from collections import Counter

import logging
logging.basicConfig()
baseLoggingLevel = logging.INFO

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

_debugQueries = []

def lower(string):
    if string:
        string = string.strip().lower()
    return string

def clean(string):
    if string:
        string = string.strip().lower().replace(' ','').replace('_','')
    return string

def get_col_name(col):
    name = col[props.EXPR_NAME]
    actual = col[props.EXPR_ACTUAL]
    # has_alias = col[props.EXPR_HAS_ALIAS]
    if name:
        return name
    else:
        return actual

def get_col_alias(col):
    name = col[props.EXPR_NAME]
    has_alias = col[props.EXPR_HAS_ALIAS]
    if has_alias:
        return name
    else:
        return None

func_pattern = re.compile(r'(?P<name>\w+)\s*\((?P<args>.*)\)$')
def get_col_table_field(col, aliases):
    actual = col[props.EXPR_ACTUAL]
    table = None
    field = None
    match = func_pattern.match(actual)
    if not match and "." in actual:
        parts = actual.split(".")
        # table = lower(parts[0])
        table = parts[0]
        if table in aliases:
            table = aliases[table]
        # field = lower(parts[1])
        field = parts[1]
    return table, field

def func(col):
    actual = col[props.EXPR_ACTUAL]
    name = None
    match = func_pattern.match(actual)
    if match:
        name = lower(match.group('name'))    
    return name

dirname = Path(getcwd()).name


with open(fullpath(props.FULL_CHECK_FILENAME)) as fi:
    query_data = json.load(fi)

databases = query_data[props.ALL_DATABASES]

for dbname, dbfilename in databases.items():
    logger.debug(f"Resetting {dbname}...")
    file = fullpath(dbfilename)
    resetDatabase(dbname, file)

logger.debug(f"Executing tests...")

queries = query_data[props.ALL_QUERIES]
num_queries = 0
raw_feedback = []
query_feedback = []

class StopException(Exception):
    pass

for query_name, expected_props in queries.items():

    debug_query = query_name in _debugQueries
    if debug_query:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug(f"Forcing DEBUG level on {query_name}")
    else:
        logging.getLogger().setLevel(baseLoggingLevel)

    is_select = expected_props.get(props.SQL_VERB) == 'select'

    raw_issues = []
    issues = []
    info = []
    stu_props = dict(expected_props)

    if '#' not in query_name:
        num_queries += 1

    # Outer TRY block to allow "continuing" the loop while still adding issues
    # at the end
    try:

        sql = ''

        try:
            with open(query_name + '.sql') as fi:
                sql = fi.read()
        except Exception as ex:
            issues.append(f"Error reading SQL file: {ex}")
            raise StopException()
        
        try:
            sql = parseSQL(sql, stu_props)
            logger.debug(sql)
        except Exception as ex:
            issues.append(f"Error parsing SQL: {ex}")
            logger.debug(f"Error parsing SQL: {ex}")
            raise StopException()

        if len(sql) == 0:
            verb = stu_props.get(props.SQL_VERB)
            if verb:
                raw_issues.append({'issue': props.SQL_VERB})
                issues.append(f"Unknown SQL verb {verb.upper()}")
                logger.debug(f"Unknown SQL verb {verb.upper()}")
            else:
                raw_issues.append({'issue': props.EMPTY})
                issues.append("EMPTY")
                logger.debug("EMPTY")

        else:

            try:
                # copy expectedprops to fill in
                logger.debug("expected_props: " + pformat(expected_props))
                getProperties(sql, stu_props)
                logger.debug("stu_props: " + pformat(stu_props))
            except Exception as ex:
                issues.append(f"Error executing SQL: {ex}")
                logger.debug(f"Error executing SQL: {ex}")
                raise StopException()
        
            if is_select:
                # create a column map to try handle cases where students add aliases
                # when not needed / wanted or aliases with/without spaces.

                exp_col_names = expected_props.get(props.COLUMN_NAMES)
                exp_cols = expected_props.get(props.SELECT_EXPRESSIONS)
                exp_tables = expected_props.get(props.TABLES)
                exp_table_names = [lower(t[props.TABLE_NAME]) for t in exp_tables]
                exp_table_dups = {k: 0 for k, v in Counter(exp_table_names).items() if v > 1}
                exp_aliases = {}
                for table in exp_tables:
                    if props.TABLE_ALIAS in table:
                        name = table[props.TABLE_NAME]
                        alias = table[props.TABLE_ALIAS]
                        if name in exp_table_dups:
                            counter = exp_table_dups[name]
                            exp_table_dups[name] = counter + 1
                            name = name + "_" + str(counter)
                        exp_aliases[alias] = name
                
                stu_cols = stu_props.get(props.SELECT_EXPRESSIONS)
                stu_tables = stu_props.get(props.TABLES)
                stu_table_names = [lower(t[props.TABLE_NAME]) for t in stu_tables]
                stu_table_dups = {k: 0 for k, v in Counter(stu_table_names).items() if v > 1}
                stu_aliases = {}
                for table in stu_tables:
                    if props.TABLE_ALIAS in table:
                        name = table[props.TABLE_NAME]
                        alias = table[props.TABLE_ALIAS]
                        if name in stu_table_dups:
                            counter = stu_table_dups[name]
                            stu_table_dups[name] = counter + 1
                            name = name + "_" + str(counter)
                        stu_aliases[alias] = name

                logger.debug('EXPECTED ALIASES:\n' + pformat(exp_aliases))
                logger.debug('STUDENT ALIASES:\n' + pformat(stu_aliases))
                
                col_map = []

                # FIRST PASS (exact and high confidence matches)

                logger.debug(f"TESTING {query_name}")
                
                for i in range(len(exp_cols)):
                    col_map.append(None)

                    exp_col = exp_cols[i]
                    logger.debug(f"exp_col: {pformat(exp_col)}")

                    exp_col_name = get_col_name(exp_col)
                    logger.debug(f"exp_col_name: {exp_col_name}")

                    exp_col_alias = get_col_alias(exp_col)
                    logger.debug(f"exp_col_alias: {exp_col_alias}")

                    exp_col_clean = clean(exp_col[props.EXPR_NAME])
                    exp_col_actual = exp_col[props.EXPR_ACTUAL]
                    exp_col_has_alias = exp_col[props.EXPR_HAS_ALIAS]

                    exp_col_table, exp_col_field = get_col_table_field(exp_col, exp_aliases)

                    logger.debug(f"EXPECTED: {exp_col_table}.{exp_col_field}")


                    for j in range(len(stu_cols)):
                        if j in col_map:
                            continue

                        stu_col = stu_cols[j]
                        stu_col_name = get_col_name(stu_col)
                        stu_col_alias = get_col_alias(stu_col)
                        stu_col_clean = clean(stu_col[props.EXPR_NAME])
                        stu_col_actual = stu_col[props.EXPR_ACTUAL]
                        stu_col_has_alias = stu_col[props.EXPR_HAS_ALIAS]

                        stu_col_table, stu_col_field = get_col_table_field(stu_col, stu_aliases)

                        logger.debug(f"STUDENT: {stu_col_table}.{stu_col_field}")

                        # First, if both queries specify aliases and they are
                        # similar, call it a match
                        if exp_col_alias and stu_col_alias and clean(exp_col_alias) == clean(stu_col_alias):
                            col_map[i] = j
                            if lower(exp_col_alias) == lower(stu_col_alias):
                                logger.debug(f'+ EXACT ALIAS: {exp_col_alias} == {stu_col_alias}')
                            else:
                                logger.debug(f'+ CLEAN ALIAS: {exp_col_alias} == {stu_col_alias}')
                                info.append(f'Unexpected alias {stu_col_alias} found for {exp_col_alias}')
                                raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_alias})
                            break

                        # Next, if table.field notation is used, we can be
                        # certain to choose the right column
                        if exp_col_field and stu_col_field:
                            if exp_col_field == stu_col_field and exp_col_table == stu_col_table:
                                logger.debug(f'- FIELD MATCH: {exp_col_table}.{exp_col_field} == {stu_col_table}.{stu_col_field} ({exp_col_name})')
                                col_map[i] = j
                                
                                # Now compare names to get alias comparison as needed
                                if lower(exp_col_name) != lower(stu_col_name):
                                    if stu_col_has_alias:
                                        info.append(f'Unexpected alias {stu_col_name} found for {exp_col_name}')
                                    else:
                                        issues.append(f'Missing alias {exp_col_name} for {stu_col_name}')
                                    raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                                break
                            else:
                                continue
                                                    # if the col names match, then just assume we've found a
                        # Find exact name matches
                        if exp_col_name and lower(exp_col_name) == lower(stu_col_name):
                            logger.debug(f'+ EXACT COLUMN: {exp_col_name} == {stu_col_name}')
                            col_map[i] = j
                            break

                        # if the col names match after removing spaces and
                        # underscores, then also assume a match (likely an alias
                        # added that matches the column name)
                        if exp_col_clean and exp_col_clean == stu_col_clean:
                            logger.debug(f'- CLEAN COLUMN: {exp_col_clean} == {stu_col_clean}')
                            col_map[i] = j
                            info.append(f'Unexpected alias {stu_col_name} found for {exp_col_name}')
                            raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                            break

                        # if the actual expressions match, we've found a match
                        if exp_col_actual and clean(exp_col_actual) == clean(stu_col_actual):
                            logger.debug(f'+ EXACT: {exp_col_actual} == {stu_col_actual}')
                            col_map[i] = j
                            if stu_col_has_alias:
                                info.append(f'Unexpected alias {stu_col_name} found for {exp_col_actual}')
                                raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                            elif exp_col_has_alias:
                                issues.append(f'Missing alias {exp_col_name} for {stu_col_actual}')
                                raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                            break

                        # One is dotted the other is not...fuzzier but still confident
                        if exp_col_field or stu_col_field:
                            if exp_col_field == lower(stu_col_actual) or stu_col_field == lower(exp_col_actual):
                                logger.debug(f'- MISSING ALIAS: {stu_col_clean} == {exp_col_field} ({exp_col_name})')
                                col_map[i] = j
                                if stu_col_has_alias:
                                    info.append(f'Unexpected alias {stu_col_name} found for {exp_col_actual}')
                                    raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                                elif exp_col_has_alias:
                                    issues.append(f'Missing alias {exp_col_name} for {stu_col_actual}')
                                    raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                                break

                # SECOND PASS (try our best)

                for i in range(len(exp_cols)):
                    if col_map[i] != None:
                        continue

                    exp_col = exp_cols[i]
                    exp_col_name = get_col_name(exp_col)
                    sep_col_clean = clean(exp_col[props.EXPR_NAME])
                    exp_col_actual = exp_col[props.EXPR_ACTUAL]
                    exp_col_has_alias = exp_col[props.EXPR_HAS_ALIAS]

                    exp_col_func = None
                    
                    match = func_pattern.match(exp_col_actual)
                    if match:
                        exp_col_func = lower(match.group('name'))

                    for j in range(len(stu_cols)):
                        if j in col_map:
                            continue

                        stu_col = stu_cols[j]
                        stu_col_name = get_col_name(stu_col)
                        stu_col_clean = clean(stu_col[props.EXPR_NAME])
                        stu_col_actual = stu_col[props.EXPR_ACTUAL]
                        stu_col_has_alias = stu_col[props.EXPR_HAS_ALIAS]

                        stu_col_func = None

                        match = func_pattern.match(stu_col_actual)
                        if match:
                            stu_col_func = lower(match.group('name'))

                        # if the funcs match, then we'll also assume a match
                        logger.debug(exp_col_func, stu_col_func)
                        if exp_col_func and exp_col_func == stu_col_func:
                            logger.debug(f'- FUNC MATCH: {exp_col_func} = {stu_col_func} ({exp_col_name})')
                            col_map[i] = j
                            if stu_col_has_alias:
                                info.append(f'Unexpected alias {stu_col_name} found for {exp_col_actual}')
                                raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                            elif exp_col_has_alias:
                                issues.append(f'Missing alias {exp_col_name} for {stu_col_actual}')
                                raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})
                            break

                    # At this point, we give up
                    if col_map[i] == None:
                        issues.append(f"Expected to find a column named {exp_col_name}")
                        raw_issues.append({'issue': props.COLUMN_NAMES, 'val': exp_col_name})

                logger.debug("col_map: " + pformat(col_map))
            
            for prop_name, exp_prop in expected_props.items():
                if prop_name not in props.FULL_PROPS:
                    continue
                
                exp_prop = expected_props[prop_name]

                stu_prop = stu_props[prop_name]
                friendly = props.friendly(prop_name)
                
                if prop_name in (props.SELECT_HAS_AS, props.FROM_HAS_AS):
                    if stu_prop == False:
                        raw_issues.append({'issue': prop_name})
                        issues.append(friendly)
                elif prop_name in (props.FIRST_ROW, props.LAST_ROW):
                    for i in range(len(exp_prop)):
                        exp_val = exp_prop[i]
                        col_name = exp_col_names[i]
                        if col_map[i] != None:
                            stu_index = col_map[i]
                            stu_val = stu_prop[stu_index]
                            if exp_val.lower() == stu_val.lower():
                                continue
                        raw_issues.append({'issue': friendly, 'val': col_name})
                        issues.append(f"Expected to find {exp_val} in {col_name} for {friendly}")
                elif type(exp_prop) is str:
                    if exp_prop.lower() != stu_prop.lower():
                        raw_issues.append({'issue': friendly, 'col': stu_prop})
                        issues.append(f"Expected {exp_prop} for {friendly} but retrieved {stu_prop}")
                else:
                    if exp_prop != stu_prop:
                        raw_issues.append({'issue': friendly, 'col': stu_prop})
                        issues.append(f"Expected {exp_prop} for {friendly} but retrieved {stu_prop}")
    except StopException:
        pass
    except Exception as ex:
        issues.append(f"Unexpected Exception: {ex}")
        logging.exception("Unexpected exception in ridiculously gigantic try block")

    if raw_issues:
        raw_feedback.append({
            'query_name': query_name,
            'issues': raw_issues,
            'sql': sql
        })

    query_feedback.append({
        'query_name': query_name,
        'issues': issues,
        'info': info,
        'student_sql': sql,
        'solution_sql': expected_props[props.SOLUTION]
    })

logger.debug("query_feedback: " + pformat(query_feedback))

logger.debug(f'...writing issues to {props.FEEDBACK_DATA_FILENAME}')
with open(props.FEEDBACK_DATA_FILENAME, 'w') as fi:
    fi.write(json.dumps(raw_feedback, indent=2))

if isfile(props.FEEDBACK_FILENAME):
    logger.info(f"SKIPPING: {dirname} because {props.FEEDBACK_FILENAME} already exists")
    exit(0)

points_per_query = round(100 / num_queries)

logger.debug(f'...writing issues to {props.FEEDBACK_FILENAME}')
with open(props.FEEDBACK_FILENAME, 'w') as fi:

    fi.write("# FEEDBACK\n")
    fi.write("\n")

    for query in query_feedback:
        fi.write('-'*78 + '\n')
        query_name = query['query_name']
        challenge_query = '#' in query_name
        info = query['info']
        issues = query['issues']

        if len(issues) == 0:
            fi.write(f"### ✓  {query_name}\n")
            wb(info, fi)
        else:
            if issues[0] == "EMPTY":
                line = f"### ✗  {query_name}"
                if not challenge_query:
                    line += f" (DEDUCTION: {points_per_query})"
                fi.write(line + "\n")
                wb(["NO QUERY PROVIDED"], fi)
            else:
                student_sql = query['student_sql']
                solution_sql = query['solution_sql']
                line = f"### ✗  {query_name}"
                if not challenge_query:
                    line += f" (DEDUCTION: )"
                fi.write(line + "\n")
                wb(info, fi)
                wb(issues, fi)
                fi.write("\n**YOUR SQL**\n")
                fi.write("\n```\n")
                fi.write(student_sql)
                fi.write("\n```\n")
                fi.write("\n**SOLUTION SQL**\n")
                fi.write("\n```\n")
                fi.write(solution_sql)
                fi.write("\n```\n\n")

logger.info(f"{len(queries)} checked for {dirname}")
