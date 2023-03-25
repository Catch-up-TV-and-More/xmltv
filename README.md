# TV guides - XMLTV

This repository keeps XMLTV TV guides up to date in order to be used with the Live TV "PVR IPTV Simple Client/Catch-up TV & More" combo.

## Notes

* Files with `_local` prefix contain all date and time in local timezone (the one from the grabber)
* Files without `_local` prefix contain all date and time in UTC

## Developers notes

The `update_all_tv_guides.sh` can be used to automatically update TV guides files (`xxxxx.xml` files).
The script automatically create a commit with the latest TV guides and it will push the modification on this GitHub repository.
This script is executed every night with a cron task but you can trigger it manually on your own computer.

## Fonctionnement (only in french ATM)

* Si on est le jour J (par exemple le 19/06/2020)
* Toutes les nuits, le script bash `update_all_tv_guides.sh` est exécuté
* Ce que fait le script bash (`update_all_tv_guides.sh`)
    * Pull du dépôt GitHub
    * Suppression des fichiers XMLTV de la racine
    * Pour chaque pays, récupération du programme TV de la journée J+2 (par exemple le 21/06/2020) qu'on place dans le dossier `raw`
    * Appel du petit script Python (`post_treatment.py`)
        * Suppression, dans le dossier `raw`, des programmes TV trop anciens
        * Fusion, pour chaque pays, des programmes TV de chaque jour présents dans le dossier `raw`
        * Post traitement des programmes TV (découpage par jour, avec heure locale ou UTC, ...)
    * Push sur le dépôt GitHub des modifications
