import mariadb as db
import props
from os import system
import regex as re
from sqlglot import parse_one, exp
from pprint import pformat as pf

import logging
logger = logging.getLogger(__name__)

# Reset a database using a SQL script
def resetDatabase(dbname, filename):
    logger.info(f"Dropping {dbname}")
    system(f'mysql -u root -e "DROP DATABASE IF EXISTS {dbname}"')
    logger.info(f"Sourcing {filename}")
    system(f'mysql -u root -e "SOURCE {filename}"')

# sl_comment_pattern = re.compile(r'(\/\/|--).*')
full_line_comment_pattern = re.compile(r'^\s*(#|--|\/\/).*', re.MULTILINE)
end_of_line_comment_pattern = re.compile(r'(#|--|\/\/)[^"\n\r]*(?:"[^"\n\r]*"[^"\n\r]*)*[\r\n]', re.MULTILINE)
multiline_comment_pattern = re.compile(r'\/\*.*?(\*\/|$)', re.DOTALL)

# Remove comments and blank lines from SQL
def removeComments(sql):
    sql = multiline_comment_pattern.sub('', sql)
    sql = full_line_comment_pattern.sub('', sql)
    logger.debug('Full Line:\n' + sql)
    sql = end_of_line_comment_pattern.sub('', sql)
    logger.debug('End of Line:\n' + sql)
    return sql

# Pull (potentially) multiple queries from a file. Though incorrect, be
# resilient to queries that have blank lines in between, as the MySQL plugin
# treats line-separated queries as separate.
def getQueries(sql):
    sql = removeComments(sql)
    queries = []
    sql_lines = []
    blank_line_count = 0
    for line in sql.splitlines():
        end = False
        line = line.rstrip()
        strip_line = line.lstrip()
        if len(strip_line) > 0:
            blank_line_count = 0
            if line.endswith(';'):
                line = line[:-1]
                end = True
            sql_lines.append(line)
        else:
            # tolerate a single blank line before assuming a new query
            if len(sql_lines) > 2 and blank_line_count > 0:
                end = True
            else:
                blank_line_count += 1
        
        # Dump the query lines
        if end:
            queries.append('\n'.join(sql_lines))
            sql_lines.clear()
    
    # Get the last query if not semi-colon or blank-line terminated
    if sql_lines:
        queries.append('\n'.join(sql_lines))

    return queries


# Fully parse a SELECT query to retrieve pertinent properties
def parseSelect(sql, properties):
    glot = parse_one(sql,read="mysql")
    
    # these determine a value for the whole query
    select_has_count_star = False
    select_has_as = None
    from_has_as = None

    # process the SELECT clause
    expressions = []
    for expr in glot.expressions:
        expression = {}
        expression[props.EXPR_NAME] = expr.alias_or_name
        expression[props.EXPR_HAS_ALIAS] = False

        if type(expr) is exp.Alias:
            expression[props.EXPR_HAS_ALIAS] = True
            if ' as ' in expr.sql().lower():
                expression[props.HAS_AS] = True
                select_has_as = select_has_as is None or select_has_as and True
            else:
                expression[props.HAS_AS] = False
                select_has_as = False
            expr = expr.unalias()

        expression[props.EXPR_ACTUAL] = expr.sql()

        for node in expr.walk():
            if type(node) is exp.Count:
                if node.this.is_star:
                    expression[props.HAS_COUNT_STAR] = select_has_count_star = True
                else:
                    expression[props.HAS_COUNT_STAR] = False

        expressions.append(expression)

    # process the FROM clause
    tables = []
    for tab in glot.find_all(exp.Table):
        table = {}
        table[props.TABLE_NAME] = tab.name
        if tab.alias:
            table[props.TABLE_ALIAS] = tab.alias
            if ' as ' in tab.sql().lower():
                table[props.HAS_AS] = True
                from_has_as = from_has_as is None or from_has_as and True
            else:
                table[props.HAS_AS] = False
                from_has_as = False
        
        tables.append(table)
    
    properties[props.SELECT_EXPRESSIONS] = expressions
    properties[props.TABLES] = tables
    properties[props.HAS_COUNT_STAR] = select_has_count_star
    properties[props.SELECT_HAS_AS] = select_has_as
    properties[props.FROM_HAS_AS] = from_has_as


# Return the _first_ SELECT/INSERT/UPDATE/DELETE query. As appropriate, also
# fills the database name, verb, and table properties as well as all "parsed"
# properties of a SELECT query.
def parseSQL(sql, properties = {}):
    properties[props.SQL_VERB] = ''

    sql_queries = getQueries(sql)

    for query_sql in sql_queries:
        words = query_sql.split()
        sql_verb = words[0].strip().lower()

        properties[props.SQL_VERB] = sql_verb

        match sql_verb:
            case 'use':
                properties[props.DATABASE_NAME] = words[1].strip().lower()
                continue
            case 'insert':
                # because some don't add space after parens...
                word3 = words[2]
                more_words = word3.split('(')
                properties[props.MODIFIED_TABLE] = more_words[0]
            case 'update':
                properties[props.MODIFIED_TABLE] = words[1]
            case 'delete':
                properties[props.MODIFIED_TABLE] = words[2]
            case 'select':
                parseSelect(query_sql, properties)
        
        return query_sql
    return ''

# Retrieve a connection to the named database.
connections = {}
def getConnection(dbname=None):
    global connections

    if not dbname:
        return db.connect(
                host="127.0.0.1",
                port=3306,
                user='root',
                connect_timeout=1
            )

    if not dbname in connections.keys():
        connections[dbname] = db.connect(
                    host="127.0.0.1",
                    port=3306,
                    user='root',
                    database=dbname,
                    connect_timeout=1
        )
    return connections[dbname]

# Convert each item in a tuple (row) to a string so that the silly
# json.dumps() function works.
def stringifyRow(row):
    result = list(row)
    for i in range(len(result)):
        result[i] = str(result[i])
    return result

# Retrieve the properties of a given query.
def getProperties(sql, properties):
    dbname = properties[props.DATABASE_NAME]
    conn = getConnection(dbname)

    with conn.cursor() as cursor:
        cursor.execute(sql)
        try:
            data = cursor.fetchall() # throws if query doesn't have results (isn't DQL)

            # sanity props
            properties[props.ROW_COUNT] = len(data)
            properties[props.COLUMN_COUNT] = len(cursor.description)

            #full props
            properties[props.COLUMN_NAMES] = [item[0] for item in cursor.description]
            if len(data) > 0:
                properties[props.FIRST_ROW] = stringifyRow(data[0])
            if len(data) > 1:
                properties[props.LAST_ROW] = stringifyRow(data[-1])
        except:
            # assume query wasn't supposed to return rows and is thus DML
            properties['rowsAffected'] = cursor.rowcount
            conn.commit()
