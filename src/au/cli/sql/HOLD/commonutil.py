from textwrap import fill, dedent
from os.path import dirname, realpath

# print a list of items with word wrapping
def ps(lines):
    for line in lines:
        print(fill(dedent(line).strip(), 80))

# print a list of items as a wrapped bulleted list
def pb(lines):
    for line in lines:
        print(fill(line.strip(), 80, initial_indent="  • ", subsequent_indent="   "))

# write a list of items as a wrapped bulleted list to a file
def wb(lines, fi):
    for line in lines:
        fi.write(fill(line.strip(), 80, initial_indent="  * ", subsequent_indent="    "))
        fi.write('\n')

# retrieve the fill path of a file in the relative to the real path of current script
def fullpath(filename):
    path = dirname(realpath(__file__))
    return path + '/' + filename
