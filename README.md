legi.py est un module python qui peut :

- créer une base de données SQLite à partir des archives de la base LEGI
- mettre à jour automatiquement et incrémentalement cette BDD
- normaliser les titres des textes
- connecter les différentes versions d'un texte entre elles
- analyser les données pour détecter [les anomalies][anomalies]

Avoir les lois françaises dans une base SQL permet aussi d'autres choses qui ne
sont pas encore implémentées directement dans legi.py, par exemple générer des
statistiques sur l'activité législative, [trouver le texte le plus ancien encore
en vigueur][tweet-texte-plus-ancien], etc.

[![Build Status](https://travis-ci.org/Legilibre/legi.py.svg)](https://travis-ci.org/Legilibre/legi.py)

## Installation

legi.py a besoin de [`libarchive`][libarchive] et [`hunspell`][hunspell]. L'installation de ces dépendances varie selon le système d'exploitation :

- Arch Linux : `pacman -S --needed libarchive hunspell hunspell-fr`
- Mac OS X : la version de `libarchive` inclue dans Mac OS X est obsolète, vous pouvez utiliser [Homebrew](https://brew.sh/) pour installer une version récente en exécutant `brew install libarchive`, puis indiquer au module Python qu'il doit utiliser cette version en ajoutant une variable d'environnement : `export LIBARCHIVE="$(find "$(brew --cellar libarchive)" -name libarchive.13.dylib | sort | tail -1)"` (cette commande peut être ajoutée au fichier d'initialisation de votre shell, typiquement `~/.bashrc` ou `~/.zshrc`)
- Ubuntu : `sudo apt-get install libarchive13 hunspell hunspell-fr libhunspell-dev`

Une fois ces dépendances système installées, vous pouvez cloner le dépôt et utiliser `pip` pour installer les modules python nécessaires :

    git clone https://github.com/Legilibre/legi.py.git
    cd legi.py
    python -m ensurepip
    pip install -r requirements.txt

legi.py et les modules dont il dépend sont compatibles avec python 3.7, 3.8 et 3.9,
les versions antérieurs de python peuvent générer des erreurs.

legi.py peut être utilisé comme dépendance d'un autre projet, il est disponible
sous forme de paquet [dans PyPI][legi-pypi].

## Création et maintenance de la BDD

La première étape est de télécharger les archives LEGI depuis
`ftp://echanges.dila.gouv.fr/LEGI/` :

    python -m legi.download ./tarballs

La deuxième étape est la conversion des archives en base SQLite :

    python -m legi.tar2sqlite legi.sqlite ./tarballs [--raw]

Cette opération peut prendre de quelques minutes à plusieurs heures selon votre
machine et le nombre d'archives. Les deux caractéristiques importantes de votre
machine sont: le disque dur (un SSD est beaucoup plus rapide), et le processeur
(notamment sa fréquence, le nombre de cœurs importe peu car le travail n'est pas
parallèle).

La taille du fichier SQLite créé est environ 4Go (en janvier 2020).

L'option `--raw` désactive le nettoyage des données, ajoutez-la si vous avez
besoin des données LEGI brutes.

`tar2sqlite` permet aussi de maintenir votre base de données à jour, il saute
automatiquement les archives qu'il a déjà traité. En général la DILA publie une
nouvelle archive à la fin de chaque jour ouvré, vous pouvez donc programmer
votre machine pour mettre à jour la BDD du mardi au samedi pendant la nuit, par
exemple avec [cron][cron] :

    0 1 * * 2-6 ID=legi chronic ~/chemin/vers/legi.py/cron/cron.sh

(`chronic` fait partie des [`moreutils`](http://joeyh.name/code/moreutils/).)

## Fonctionnalités

### Normalisation des titres et numéros

Le module `normalize` nettoie les titres et numéros des textes, des sections et
des articles afin qu'ils soient plus « standards ».

### Factorisation des textes

La "factorisation" connecte entre elles les différentes version d'un même texte.
La base LEGI n'a pas d'identifiant qui remplisse réellement ce rôle.

### Nettoyage des contenus

Le module `html` permet de nettoyer les contenus des textes. Il supprime :

- les espaces redondantes (*whitespace collapse*), sauf à l'intérieur des `<pre>`
- les attributs inutiles, par exemple `id` et `dir="ltr"`
- les éléments inutiles, par exemple un `<span>` sans attributs
- les éléments vides, sauf `<td>` et `<th>`

En janvier 2020 il détecte 93 millions de caractères inutiles dans LEGI.

Cette fonctionnalité n'est pas activée par défaut car elle est « destructrice »
et récente. Vous pouvez nettoyer tout l'HTML d'une base en exécutant la commande
`python -m legi.html clean legi.sqlite` (les modifications ne sont enregistrées
que si vous entrez `y` à la fin).

### Détection d'anomalies

Le module `anomalies` est conçu pour détecter les incohérences dans les données afin de les signaler à la DILA. Le résultat est visible sur [anomalies.legilibre.fr][anomalies]. (`cron/anomalies-cron.sh` est le script qui génère ce mini-site.)

Pour détecter les anomalies actuellement présentes dans la base :

    python -m legi.anomalies legi.sqlite

## Contribuer

Les *Pull Requests* sont bienvenues, n'hésitez pas à [ouvrir une discussion](https://github.com/Legilibre/legi.py/issues/new) avant de commencer le travail, ça permet une meilleure coopération et coordination. Vous pouvez aussi vous présenter dans [le salon](https://github.com/Legilibre/salon).

### Tests

legi.py utilise [Tox](https://pypi.python.org/pypi/tox) pour tester le code sur plusieurs versions de Python. Installez-le si nécessaire puis lancez la commande `tox` dans le dossier qui contient votre copie du dépôt legi.py.

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
[anomalies.legilibre.fr][anomalies] fut créé.

En février 2017 la version 0.1 est publiée.


[anomalies]: http://anomalies.legilibre.fr/
[cron]: https://en.wikipedia.org/wiki/Cron
[hunspell]: https://hunspell.github.io/
[libarchive]: http://libarchive.org/
[legi-data]: https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
[legi-pypi]: https://pypi.org/project/legi/
[tweet-debut]: https://twitter.com/Changaco/statuses/484674913954172929
[tweet-texte-plus-ancien]: https://twitter.com/Changaco/statuses/491566919544479745
