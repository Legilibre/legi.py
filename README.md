# dila2sql

![DILA2SQL Logo](https://i.imgur.com/wS0w4lO.png)

Ce multirepo expose plusieurs packages:
- `dila2sql`: générer des bases SQL à partir des exports publiés au format XML par la [DILA (Direction de l’information légale et administrative)][dila].
- `dilajs`: librairie NodeJS qui permet d'accéder à une base PostgreSQL générée par `dila2sql`.
- `api`: API Express qui expose la base générée en utilisant `dila.js`

Le package `dila2sql` est un fork du projet [`legi.py`][legi.py] créé par [Legilibre][legilibre] et [@Changaco][changaco].

Les packages `api` et `dilajs` ont été initialement créés par [@revolunet][revolunet] dans le cadre du projet [`legixplore`][legixplore].
Nous les avons ensuite migrés dans ce multirepo pour des raisons pratiques et logiques.

# Usage

Suivez les instructions des README des trois packages.

## Contribuer

Les _Pull Requests_ sont bienvenues.

Les [autres bases de la DILA][dila-bases] sont disponibles dans des dumps XML similaires, il devrait donc être relativement aisé d'adapter `dila2sql` pour les supporter.

## Projets connexes

- http://github.com/Legilibre
- https://framagit.org/parlement-ouvert
- http://github.com/regardscitoyens
- https://framagit.org/tricoteuses

## Licence

[CC0 Public Domain Dedication](http://creativecommons.org/publicdomain/zero/1.0/)

[dila]: http://www.dila.premier-ministre.gouv.fr/
[legi.py]: https://github.com/Legilibre/legi.py/
[legilibre]: https://github.com/Legilibre
[changaco]: https://github.com/Changaco
[revolunet]: https://github.com/revolunet
[legixplore]: https://github.com/SocialGouv/legixplore/
[dila-bases]: https://www.dila.premier-ministre.gouv.fr/repertoire-des-informations-publiques/les-donnees-juridiques
