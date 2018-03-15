# legi.js


[![npm](https://img.shields.io/npm/v/legi.svg)](https://www.npmjs.com/package/legi)
![license](https://img.shields.io/npm/l/legi.svg)
[![github-issues](https://img.shields.io/github/issues/revolunet/legi.js.svg)](https://github.com/revolunet/legi.js/issues)


![nodei.co](https://nodei.co/npm/legi.png?downloads=true&downloadRank=true&stars=true)

Une API NodeJS pour requêter les textes de loi issus d'une base [legi.py](https://github.com/Legilibre/legi.py)

Utilise [knex](https://github.com/tgriesser/knex/) et le standard [unist](https://github.com/syntax-tree/unist) pour représenter les textes sous forme d'arbre.

Vous pouvez récupérer une version du fichier SQLite au 8 Mars 2018 ici : https://drive.google.com/open?id=1h3Q0EaxsPdP6jAkeKZplfgtXbsG4vALW (700Mo)

## Usage

Promise-based API

```js
const Legi = require('legi');

const legi = new Legi('/path/to/legi.sqlite');

// liste des codes disponibles
legi.getCodesList();

// code du travail (~3min)
legi.getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" });

// liste des versions du code du travail (dates)
legi.getCodeDates("LEGITEXT000006072050");

// ordonnance
legi.getJORF("JORFTEXT000000465978");

// section d'un texte
legi.getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" });

// conversion en markdown
const markdown = require('legi/src/markdown')
legi.getCode("LEGITEXT000006069414").then(markdown);

// conversion en html
const html = require('legi/src/html')
legi.getCode("LEGITEXT000006069414").then(html);

```

Plus d'exemples dans [./examples.js](./examples.js)

### A propos de legi.py

legi.py est un module python qui génère une base sqlite à partir de la base LEGI, normalise et consolide les données. [plus d'infos ici](https://github.com/Legilibre/legi.py).

### Utiliser Postgres

Convertir la base legilibre.sqlite dans Postgres pour de meilleures performances

⚠️ Utiliser [pgloader](https://github.com/dimitri/pgloader) avec le paramètre `--cast "type day to varchar"`

```sh
# lancer pgloader en local
pgloader --cast "type day to varchar" legilibre.sqlite postgresql://postgres:test@127.0.0.1:5433/legi
```

### Related

 - https://github.com/Legilibre/legi.py
 - https://github.com/Legilibre/Archeo-Lex
 - https://github.com/Legilibre/legi-php
 - https://github.com/revolunet/legi.py-docker
