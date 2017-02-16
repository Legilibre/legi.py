legi.py est un module python qui peut:

- créer une base de données SQLite à partir des archives de la base LEGI
- mettre à jour automatiquement et incrémentalement cette BDD
- normaliser les titres des textes
- connecter les différentes versions d'un texte entre elles
- analyser les données pour détecter [les anomalies][anomalies]

Avoir les lois françaises dans une base SQL permet aussi d'autres choses qui ne
sont pas encore implémentées directement dans legi.py, par exemple générer des
statistiques sur l'activité législative, [trouver le texte le plus ancien encore
en vigueur][tweet-texte-plus-ancien], etc.

## Installation

Vous pouvez cloner le dépôt et utiliser `pip` pour installer les modules python
nécessaires:

    git clone https://github.com/Legilibre/legi.py.git
    cd legi.py
    python -m ensurepip
    pip install -r requirements.txt

legi.py a aussi besoin de [`libarchive`][libarchive]. Pour l'installer sur Ubuntu:

    sudo apt-get install libarchive13

legi.py et les modules dont il dépend sont compatibles avec python 2 et 3.

legi.py peut être utilisé comme dépendance d'un autre projet, il est disponible
sous forme de paquet [sur PyPI][legi-pypi].

## Création et maintenance de la BDD

La première étape est de télécharger les archives LEGI depuis
`ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/`:

    python -m legi.download ./tarballs

(`wget` doit être installé pour que cela fonctionne.)

La deuxième étape est la conversion des archives en base SQLite:

    python -m legi.tar2sqlite legi.sqlite ./tarballs

Cette opération peut prendre de quelques minutes à plusieurs heures selon votre
machine et le nombre d'archives. Les deux caractéristiques importantes de votre
machine sont: le disque dur (un SSD est beaucoup plus rapide), et le processeur
(notamment sa fréquence, le nombre de cœurs importe peu car le travail n'est pas
parallèle).

La taille du fichier SQLite créé est environ 3,3Go (en février 2017).

`tar2sqlite` permet aussi de maintenir votre base de données à jour, il saute
automatiquement les archives qu'il a déjà traité. En général la DILA publie une
nouvelle archive à la fin de chaque jour ouvré, vous pouvez donc programmer
votre machine pour mettre à jour la BDD du mardi au samedi pendant la nuit, par
exemple avec [cron][cron]:

    0 1 * * 2-6 ID=legi chronic ~/chemin/vers/legi.py/cron/cron.sh

(`chronic` fait partie des [`moreutils`](http://joeyh.name/code/moreutils/).)

## Fonctionnalités

### Normalisation des titres

Le module `normalize` corrige les titres de textes qui ne sont pas parfaitement
"standards". Les données originales sont sauvegardées dans une table dédiée.

### Factorisation des textes

La "factorisation" connecte entre elles les différentes version d'un même texte.
La base LEGI n'a pas d'identifiant qui remplisse réellement ce rôle.

### Détection d'anomalies

Le module `anomalies` est conçu pour détecter les incohérences dans les données
afin de les signaler à la DILA. Le résultat est visible sur [anomalies.legilibre.fr]
[anomalies]. (`cron/anomalies-cron.sh` est le script qui génère ce mini-site.)

Pour détecter les anomalies actuellement présentes dans la base:

    python -m legi.anomalies legi.sqlite

## Licence

[CC0 Public Domain Dedication](http://creativecommons.org/publicdomain/zero/1.0/)

## Historique du projet

Fin juin 2014 la [base de données LEGI][legi-data] contenant les lois françaises
a été libérée en Open Data. J'ai immédiatement [commencé le travail][tweet-debut]
pour la convertir dans d'autres formats. Malheureusement, distrait par d'autres
choses à faire et un peu découragé par la structure médiocre des données j'ai
fini par laisser le projet de côté.

En 2015 j'ai réouvert, nettoyé et publié mon code. J'ai ensuite été très occupé
à créer [Liberapay](https://liberapay.com/).

Fin 2016 j'ai à nouveau travaillé sur legi.py. Le projet progressa fortement,
[anomalies.legilibre.fr][anomalies] fût créé.

En février 2017 la version 0.1 est publiée.


[anomalies]: http://anomalies.legilibre.fr/
[cron]: https://en.wikipedia.org/wiki/Cron
[libarchive]: http://libarchive.org/
[legi-data]: https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
[legi-pypi]: https://pypi.python.org/pypi/legi
[tweet-debut]: https://twitter.com/Changaco/statuses/484674913954172929
[tweet-texte-plus-ancien]: https://twitter.com/Changaco/statuses/491566919544479745
