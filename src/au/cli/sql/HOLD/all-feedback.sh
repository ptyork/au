#!/usr/bin/bash

pwd=$PWD

for file in */
do
    if [[ $file != .* ]] && [[ $file != _* ]]
    then
        echo "GENERATING FEEDBACK FOR ${file}"
        cd $file
        $pwd/_solution_/.sanity-check/feedback.py
        cd ..
    fi
done
