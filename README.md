# TV guides - XMLTV

This repository keeps XMLTV TV guides up to date in order to be used with the Live TV "PVR IPTV Simple Client/Catch-up TV & More" combo.

## Notes

* Files with `_local` prefix contain all date and time in local timezone (the one from the grabber)
* Files without `_local` prefix contain all date and time in UTC

## Developers notes

Contrary to what the name suggests, the `master` branch is not the default 
branch in this repo. It contains no code, just EPG data files. The default 
branch is `dev`, which contains all code and no data. All PR's should target 
the `dev` branch.

The `update_all_tv_guides.py` script can be used to automatically update TV 
guides files (`xxxxx.xml` files). This script is executed every night from a 
GitHub workflow that is triggered by a cron task, but you can run it manually 
on your own computer. The workflow automatically create a commit with the 
latest TV guides and it will push the modifications to the master branch on 
this GitHub repository.

## How it works

* Every night at 22:00 the workflow runs.
* Pull the `dev` branch from the GitHub repo.
* Pull the `master` branch from the GitHub repo and copy the folder with raw 
  files.
* Python script `update_all_tv_guides.py` is executed
* What the script does (`update_all_tv_guides.py`):
  * Delete XMLTV files from the root directory
  * Deletes outdated files from the `raw` folder
  * For each country, always retrieve the file with TV programmes for tomorrow 
    and place it in the `raw` folder.
  * Determine how many days of EPG should be available for each country and 
    retrieve the programmes for each day for which no raw file is yet available. 
  * Calls the small Python script (`post_treatment.py`)
  * Merges the TV programmes for each day in the `raw` folder for each country
  * Post-processes the TV programmes (divides them by day, with local time or UTC, etc.)
* Pushes xmltv files and raw files to the master branch of the GitHub repository
