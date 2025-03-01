# Query Property Constants

# collection
ALL_DATABASES = 'databases'
ALL_QUERIES = 'queries'

# per query
DATABASE_NAME = 'dbname'
SOLUTION = 'solution'

# parsed
EMPTY = 'empty'
SQL_VERB = 'verb'
SELECT_EXPRESSIONS = 'expressions'
HAS_COUNT_STAR = "hasStar"
SELECT_HAS_AS = 'selectHasAs'
FROM_HAS_AS = 'fromHasAs'
EXPR_NAME = "name"
EXPR_ACTUAL = 'actual'
EXPR_HAS_ALIAS = 'hasAlias'
TABLES = "tables"
TABLE_NAME = 'name'
TABLE_ALIAS = 'alias'
HAS_AS = 'hasAs'
MODIFIED_TABLE = 'modifiedTable'

# execution results

# DQL
ROW_COUNT = 'rowCount'
COLUMN_COUNT = 'colCount'
COLUMN_NAMES = 'colNames'
FIRST_ROW = 'firstRow'
LAST_ROW = 'lastRow'

# DML
TABLE_NAME = "name"
ROWS_AFFECTED = 'rowsAffected'

# Query Property Collections
SANITY_PROPS = (
    SQL_VERB,
    DATABASE_NAME,
    ROW_COUNT,
    COLUMN_COUNT,
    ROWS_AFFECTED,
    MODIFIED_TABLE
)

FULL_PROPS = (
    SQL_VERB,
    DATABASE_NAME,
    HAS_COUNT_STAR,
    SELECT_HAS_AS,
    FROM_HAS_AS,
    # DQL
    ROW_COUNT,
    COLUMN_COUNT,
    # COLUMN_NAMES,
    FIRST_ROW,
    LAST_ROW,
    # DML
    ROWS_AFFECTED,
    MODIFIED_TABLE,
)

__propToFriendlyDict__ = {
    SQL_VERB: 'sql verb',
    DATABASE_NAME: 'database name',
    HAS_COUNT_STAR: "uses COUNT(*) to count records",
    SELECT_HAS_AS: 'use AS keyword for all aliases in SELECT clause',
    FROM_HAS_AS: 'use AS keyword for all aliases in FROM clause',
    ROW_COUNT: 'number of rows',
    COLUMN_COUNT: 'number of columns',
    ROWS_AFFECTED: 'rows affected',
    MODIFIED_TABLE: 'table name',
    FIRST_ROW: 'first row',
    LAST_ROW: 'last row'
}

def friendly(propName):
    friendlier = propName.lower().replace('_',' ')
    friendly = __propToFriendlyDict__.setdefault(propName, friendlier)
    return friendly

# Filenames
SANITY_CHECK_FILENAME = 'sanitycheck.json'
FULL_CHECK_FILENAME = 'fullcheck.json'
FEEDBACK_FILENAME = 'FEEDBACK.md'
FEEDBACK_DATA_FILENAME = '.sanity-check/raw-feedback.json'

TEMPLATE_DIRECTORY = '_template_'
SOLUTION_DIRECTORY = '_solution_'
