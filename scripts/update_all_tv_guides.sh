#!/usr/bin/env bash

# Move in the scripts directory
BASEDIR=$(dirname "$0")
cd $BASEDIR
BASEDIR=$(pwd) # Only to get absolute path and not relative path

now=$(date +"%d/%m/%Y %H:%M:%S-%Z")

force_pull () {
    git fetch --all
    git reset --hard "origin/$BRANCH"
}

force_push () {
    git add --all
    git commit --amend -m "Auto update TV guides ($now)"
    git push -f origin master
}


move_log_file () {
    # If this script was executed with the
    # command './update_all_tv_guides.sh 2>&1 | tee /tmp/xmltv_log.txt'
    if test -f "/tmp/xmltv_log.txt"; then
        mv "/tmp/xmltv_log.txt" "log.txt"
    fi
}


./update_all_tv_guides.py

move_log_file

echo -e "\n- Force push changes\n"
force_push

echo -e "\n- Changes have been pushed --> exit\n"
exit 0
