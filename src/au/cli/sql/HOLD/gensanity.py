#!/usr/bin/python3

from commonsql import parseSQL, getProperties, resetDatabase
from commonsql import logger, baseLoggingLevel
from commonutil import fullpath
from pprint import pformat as pf
import logging
import props

import json
import os
import re


_debugQueries = []

_databases = {}
_queries_full = {}
_queries_sanity = {}

while True:
    dbnum = len(_databases) + 1
    dbname = input(f'Enter name of database {dbnum} (enter to stop): ').strip().lower()
    if len(dbname) == 0:
        break
    dbfilename = input(f'Enter schema filename ({dbname}.sql): ').strip()
    if len(dbfilename) == 0:
        dbfilename = dbname + '.sql'
    _databases[dbname] = dbfilename

if len(_databases) == 0:
    exit(0)

for dbname, dbfilename in _databases.items():
    file = fullpath(dbfilename)
    resetDatabase(dbname, file)

# This mess of convolution is needed solely to sort the files
# in a logical order.

queryfiles = []
maxnums = 0
for filename in os.listdir():
    if not filename.endswith('.sql'):
        continue

    query_name = filename[:-4]
    match = re.search('(\d+)(.*)',query_name)
    if not match:
        continue

    numcount = len(match.group(1))
    if numcount > maxnums:
        maxnums = numcount

    sortname = match.group(0)
    
    queryfiles.append([sortname, query_name, numcount])

for i in range(len(queryfiles)):
    numcount = queryfiles[i][2]
    numdiff = maxnums - numcount
    if numdiff:
        queryfiles[i][0] = ('0' * numdiff) + queryfiles[i][0]

# Now done with allowing for sorting, cycle through the sorted list of queries

for _, query_name, _ in sorted(queryfiles):

    debug_query = query_name in _debugQueries
    if debug_query:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Forcing DEBUG level on {query_name}")
    else:
        logger.setLevel(baseLoggingLevel)

    logger.info(f'Processing {query_name}')
    properties_full = {}

    try:
        with open(query_name + '.sql') as fi:
            sql = parseSQL(fi.read(), properties_full)

        if len(sql) == 0:
            logger.warning(f"No SQL found for {query_name}")
            continue

        if len(_databases) == 1:
            dbname = list(_databases.keys())[0]
        else:
            if props.DATABASE_NAME in properties_full:
                dbname = properties_full[props.DATABASE_NAME]
            else:
                dbname = input("Enter dbname: ").lower().strip()

        properties_full[props.DATABASE_NAME] = dbname
        properties_full[props.SOLUTION] = sql
        getProperties(sql, properties_full)

    except OSError as ex:
        logger.exception(f"Error reading SQL file")
        exit(1)
    except Exception as ex:
        logger.exception(f"Error executing SQL")
        exit(1)

    _queries_full[query_name] = properties_full
    properties_sanity = {}
    for propname in props.SANITY_PROPS:
        if propname in properties_full.keys():
            properties_sanity[propname] = properties_full[propname]
    _queries_sanity[query_name] = properties_sanity

jsondata_full = {
    props.ALL_DATABASES : _databases,
    props.ALL_QUERIES : _queries_full
}
jsonText_full = json.dumps(jsondata_full, indent=2)

logger.debug("Full Check:\n" + jsonText_full)

jsondata_sanity = {
    props.ALL_DATABASES : _databases,
    props.ALL_QUERIES : _queries_sanity
}
jsonText_sanity = json.dumps(jsondata_sanity, indent=2)

logger.debug("Sanity Check:\n" + jsonText_sanity)

path = os.path.dirname(os.path.realpath(__file__))

jsonFilename = path + '/' + props.FULL_CHECK_FILENAME
with open(jsonFilename, mode='w') as fi:
    fi.write(jsonText_full)
print(f'Wrote {len(_queries_full)} queries to {jsonFilename}')

jsonFilename = path + '/' + props.SANITY_CHECK_FILENAME
with open(jsonFilename, mode='w') as fi:
    fi.write(jsonText_sanity)

logger.info(f'Wrote {len(_queries_full)} queries to {jsonFilename}')
