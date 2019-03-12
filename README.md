# legi.py

Fork de [Legilibre/legi.py](https://github.com/legilibre/legi.py) avec :

- gestion des bases [LEGI](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/), [KALI](https://www.data.gouv.fr/fr/datasets/kali-conventions-collectives-nationales/) et [JORF](https://www.data.gouv.fr/fr/datasets/jorf-les-donnees-de-l-edition-lois-et-decrets-du-journal-officiel/)
- Parallélisation des téléchargements
- docker (optionnel)

Les bases de données OpenData en XML sont très riches mais difficilement exploitable.

legi.py permet de convertir ces données en une base de données relationnelle, plus facilement interrogeable.

### Usage

~~Vous pouvez récupérer directement les dernières bases de données compilées ici :~~

- LEGI.sqlite
- KALI.sqlite
- JORF.sqlite

~~[badge date mise à jour]~~

~~dumps PostgreSQL également dispos sur [legi-postgres](https://github.com/SocialGouv/legi-postgres)~~

#### Docker

Si vous souhaitez créer les fichiers SQLite vous-même , vous pouvez utilisez l'image docker `socialgouv/legi.py`.

> 💡 Les volumes et temps de compilation initiale peuvent durer plusieures heures selon votre matériel/connexion.

#### Installation locale

Installez libarchive puis

```sh
pip install -r requirements.txt
```


sur Mac OS X, il vous faudra aussi probablement exporter la variable `LD_LIBRARY_PATH` à cause de ce [bug connu](https://github.com/dsoprea/PyEasyArchive#notes). Par exemple :

```sh
# ~/.zshrc
export LIBARCHIVE=/usr/local/Cellar/libarchive/3.3.3/lib/libarchive.13.dylib
```


##### Lancer le download de la base LEGI

Cette commande lance le téléchargement des bases OpenData de la DILA et les sauvegarde localement dans `./data`.

```sh
docker run --rm -t              \
    -v $PWD/data:/data          \
    socialgouv/legi.py          \
    python -m legi.download /data --base LEGI
```

##### mettre à jour le fichier SQLite de la base LEGI

Cette commande lit tous les fichiers dans `./data` et crée ou met à jour une base de données SQLite.

```sh
docker run --rm -t         \
    -v $PWD/data:/data     \
    socialgouv/legi.py     \
    python -m legi.importer /data/LEGI.sqlite /data --base LEGI
```

Le fichier sera crée localement dans `./data/legi.sqlite` via le volume docker.

#### PostgreSQL

Vous pouvez utiliser [legi-postgres](https://github.com/SocialGouv/legi-postgres) pour convertir ces données au format PostgreSQL

## Développement

Vous pouvez développer _dans_ l'environnement docker en ajoutant `-v $PWD:/app` au lancement du container :

```sh
docker run --rm -t         \
    -v $PWD/data:/data     \
    -v $PWD:/app           \
    socialgouv/legi.py     \
    python hello.py
```

### Tests

legi.py utilise [Tox](https://pypi.python.org/pypi/tox) pour tester le code sur plusieurs versions de Python. Installez-le si nécessaire puis lancez la commande `tox` dans le dossier qui contient votre copie du dépôt legi.py.

Sur Mac OS X, si vous rencontrez un bug sur libarchive quand vous lancez tox, essayez avec cette commande: `TOX_TESTENV_PASSENV=LIBARCHIVE tox`

## A propos

legi.py permet de :

- créer une base de données SQLite à partir des archives des bases LEGI, KALI, JORF
- mettre à jour automatiquement et incrémentalement cette BDD
- normaliser les titres des textes
- connecter les différentes versions d'un texte entre elles
- analyser les données pour détecter [les anomalies][anomalies]

Plus d'informations sur le [repo original](https://github.com/Legilibre/legi.py)

## Contribuer

Les _Pull Requests_ sont bienvenues. Vous pouvez aussi ouvrir des PRs sur le [repo original de Legilibre](https://github.com/Legilibre/legi.py)

## Projets connexes

- http://github.com/Legilibre
- https://framagit.org/parlement-ouvert
- http://github.com/regardscitoyens
- https://framagit.org/tricoteuses

## Licence

[CC0 Public Domain Dedication](http://creativecommons.org/publicdomain/zero/1.0/)

[anomalies]: http://anomalies.legilibre.fr/
[cron]: https://en.wikipedia.org/wiki/Cron
[libarchive]: http://libarchive.org/
[legi-data]: https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
[legi-pypi]: https://pypi.python.org/pypi/legi
[tweet-debut]: https://twitter.com/Changaco/statuses/484674913954172929
[tweet-texte-plus-ancien]: https://twitter.com/Changaco/statuses/491566919544479745
