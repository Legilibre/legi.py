# legi.js


[![npm](https://img.shields.io/npm/v/legi.svg)](https://www.npmjs.com/package/legi)
![license](https://img.shields.io/npm/l/legi.svg)
[![github-issues](https://img.shields.io/github/issues/revolunet/legi.js.svg)](https://github.com/revolunet/legi.js/issues)


![nodei.co](https://nodei.co/npm/legi.png?downloads=true&downloadRank=true&stars=true)

Une API NodeJS pour requêter les textes de loi issus d'une base [legi.py](https://github.com/Legilibre/legi.py)

Utilise [knex](https://github.com/tgriesser/knex/) et le standard [unist](https://github.com/syntax-tree/unist) pour représenter les textes sous forme d'arbre, de HTML, ou de markdown

Vous pouvez récupérer une version du fichier SQLite au 8 Mars 2018 ici : https://drive.google.com/open?id=1h3Q0EaxsPdP6jAkeKZplfgtXbsG4vALW (700Mo)

## Usage

Promise-based API

```js
const Legi = require('legi');

// defaults to ./legi.sqlite
const legi = new Legi('/path/to/legi.sqlite');

// liste des codes disponibles
legi.getCodesList().then(console.log);

// code du travail (~3min)
legi.getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" }).then(console.log);

// liste des versions du code du travail
legi.getCodeVersions("LEGITEXT000006072050").then(console.log);

// journal officiel
legi.getJORF("JORFTEXT000000465978").then(console.log);

// section d'un texte
legi.getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" }).then(console.log);

// conversion en markdown
const markdown = require('legi/src/markdown');
legi.getCode("LEGITEXT000006069414").then(markdown).then(console.log);

// conversion en html
const html = require('legi/src/html');
legi.getCode("LEGITEXT000006069414").then(html).then(console.log);

```

Plus d'exemples dans [./examples](./examples)

### A propos de legi.py

legi.py est un module python qui génère une base sqlite à partir de la base LEGI, normalise et consolide les données. [plus d'infos ici](https://github.com/Legilibre/legi.py).

### Utiliser Postgres

Convertir la base legilibre.sqlite dans Postgres pour de meilleures performances

Exemple avec l'[image docker](https://github.com/revolunet/legi.py-docker)

## Todo

 - versions et liens dans getArticle
 - caching middleware

### Related

 - https://github.com/Legilibre/legi.py
 - https://github.com/Legilibre/Archeo-Lex
 - https://github.com/Legilibre/legi-php
 - https://github.com/revolunet/legi.py-docker
