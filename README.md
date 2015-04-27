## Installation

Les scripts ici présents nécessitent [`libarchive`][libarchive] ainsi que les
modules python listés dans `requirements.txt`. Les scripts et leurs dépendances
sont tous compatibles avec python 2 et 3.

## Utilisation

La première étape est de télécharger les archives LEGI depuis
`ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/`.

La deuxième étape est la conversion des archives en base SQLite avec le script
`tar2sqlite.py`. D'abord la première grosse archive:

    python tar2sqlite.py Freemium_legi_global_*.tar.gz legi.sqlite

puis les autres petites archives, s'il y en a:

    for f in legi_*.tar.gz; do python tar2sqlite.py $f legi.sqlite; done

Maintenant que vous avez les données dans une base SQLite vous pouvez exécuter
d'autres scripts mais pour le moment le seul qui soit réellement utile est
`anomalies.py` qui est conçu pour détecter les incohérences dans les données
afin de les signaler à la DILA.

## Licence

GPLv3 (or any later version)

## Historique du projet

Fin juin 2014 la [base de données LEGI][legi] contenant toutes les lois
françaises en vigueur a été libéré en Open Data. J'ai immédiatement [commencé le
travail][tweet] pour la convertir dans d'autres formats. Malheureusement,
distrait par d'autres choses à faire et un peu découragé par la structure
médiocre des données j'avais temporairement laissé le projet de côté.

Suite à [un billet de blog qui a fait du bruit][korben] j'ai découvert que
d'autres projets similaires sont apparus entre temps:

- [Seb35/Archeo-Lex](https://github.com/Seb35/Archeo-Lex/)
- [steeve/france.code-civil](https://github.com/steeve/france.code-civil)

ce qui m'a poussé à réouvrir, nettoyer et publier mon code.


[libarchive]: http://libarchive.org/
[legi]: https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
[tweet]: https://twitter.com/Changaco/statuses/484674913954172929
[korben]: http://korben.info/10-etapes-pour-pirater-la-france.html
