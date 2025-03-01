#!/usr/bin/python3

###############################################################################
# 
#   D O   N O T   M O D I F Y   T H I S   F I L E
# 
###############################################################################
# 
# You can run it from the terminal by entering:
# 
#      ./checkit
# 
# and pressing enter. Or just hit the 󠁆▷ button to run it if you're simply not
# cool enough to type terminal commands.
# 
###############################################################################

from commonutil import ps, pb, fullpath
from commonsql import resetDatabase, parseSQL, getProperties
import props
import json

ps([
    'SANITY CHECK',
    '============',
    '''
        This script tests only basic properties of your SQL queries. It is meant
        only to prevent major blunders. Any given test may "pass" and you may
        still have significant errors in your SQL.
    '''
])
print()

with open(fullpath(props.SANITY_CHECK_FILENAME)) as fi:
    querydata = json.load(fi)

databases = querydata[props.ALL_DATABASES]

for dbname, dbfilename in databases.items():
    print(f"Resetting {dbname} database...")
    file = fullpath(dbfilename)
    resetDatabase(dbname, file)

print(f"Executing tests...")

queries = querydata[props.ALL_QUERIES]
queryissues = {}

for queryname, expectedprops in queries.items():

    issues = []
    actualprops = dict(expectedprops)

    try:
        with open(queryname + '.sql') as fi:
            sql = parseSQL(fi.read(), actualprops)

        if len(sql) == 0:
            verb = actualprops.setdefault(props.SQL_VERB, None)
            if verb:
                issues.append(f"Unknown SQL verb {verb.upper()}")
            else:
                issues.append("EMPTY")

        else:

            # copy expectedprops to fill in
            getProperties(sql, actualprops)
        
            # print(expectedprops)
            verb = expectedprops['verb']

            for propname, exp in expectedprops.items():
                exp = expectedprops[propname]
                act = actualprops[propname]
                friendly = props.friendly(propname)
                if exp != act:
                    issues.append(f"Expected {exp} for {friendly} but retrieved {act}")

    except OSError as ex:
        issues.append(f"Error reading SQL file: {ex}")
    except Exception as ex:
        issues.append(f"Error executing SQL: {ex}")

    queryissues[queryname] = issues


print()

total = len(queries)
passed = 0
failed = 0
empty = 0

for queryname, issues in queryissues.items():
    if len(issues) == 0:
        print(f"  ✓  {queryname}")
        passed += 1
    else:
        if issues[0] == "EMPTY":
            print(f"  _  {queryname} (NO SQL PROVIDED)")
            empty += 1
        else:
            print(f"  ✗  {queryname}")
            failed += 1
            pb(issues)

print()
print( '╔══════════════════════╗')
print(f"║ queries checked: {total:3} ║")
print( '╟──────────────────────╢')
print(f"║          passed: {passed:3} ║")
print(f"║          failed: {failed:3} ║")
print(f"║           empty: {empty:3} ║")
print( '╚══════════════════════╝')
print()




