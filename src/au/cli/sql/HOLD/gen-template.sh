#!/usr/bin/bash

pwd=$PWD

solution=./_solution_
template=./_template_
end_instruction_pattern="/$W R I T E/q"

#####################################################################
echo "** REMOVING EVERYTHING FROM $template (except .git/) **"

for entry in $template/*; do
    if [ -f $entry ]; then
        rm -f $entry
    else
        rm -rf $entry
    fi
done
for entry in $(echo $template/.[^.]*); do
    if [ -f $entry ]; then
        rm -f $entry > /dev/null
    elif [[ $entry != *".git"* ]]; then
        rm -rf $entry > /dev/null
    fi
done

#####################################################################
echo "** COPYING EVERYTHING FROM $solution (except .git/) **"

# Folders
for entry in $solution/*; do
    if [ -d $entry ]; then
        echo "COPYING $entry"
        cp -r $entry $template > /dev/null
    fi
done
# .files and .folders
for entry in $(echo $solution/.[^.]*); do
    if [ -f $entry ]; then
        echo "COPYING $entry"
        cp $entry $template > /dev/null
    elif [[ $entry != *".git"* ]]; then
        echo "COPYING $entry"
        cp -r $entry $template > /dev/null
    fi
done

echo "REMOVING SOLUTION-ONLY FILES"

rm -f $template/.sanity-check/feedback.py
rm -f $template/.sanity-check/feedback_score.py
rm -f $template/.sanity-check/fullcheck.json
rm -f $template/.sanity-check/gensanity.py

# all other files
for file in $solution/*; do
    if [ -f $file ]; then
        if [[ $file == *.sql ]]; then
            name=${file##*/}
            echo PROCESSING ${file}
            sed "${end_instruction_pattern}" $file > $template/$name
            echo >> $template/$name
        else
            echo COPYING ${file}
            cp $file $template
        fi
    fi
done
