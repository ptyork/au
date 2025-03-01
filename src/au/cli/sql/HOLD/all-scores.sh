#!/usr/bin/bash

pwd=$PWD

for file in */
do
    if [[ $file != .* ]] && [[ $file != _* ]]
    then
        echo "CALCULATING SCORES FOR ${file}"
        cd $file
        $pwd/_solution_/.sanity-check/feedback_score.py
        cd ..
    fi
done
