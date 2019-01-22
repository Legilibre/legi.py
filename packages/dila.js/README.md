# legi.js [![experimental](http://badges.github.io/stability-badges/dist/experimental.svg)](http://github.com/badges/stability-badges)

[![npm](https://img.shields.io/npm/v/legi.svg)](https://www.npmjs.com/package/legi)
![license](https://img.shields.io/npm/l/legi.svg)
[![github-issues](https://img.shields.io/github/issues/revolunet/legi.js.svg)](https://github.com/revolunet/legi.js/issues)

[![nodei.co](https://nodei.co/npm/legi.png?downloads=true&downloadRank=true&stars=true)](https://www.npmjs.com/package/legi)

Une API NodeJS pour requêter les textes de loi bruts issus d'une base [legi.py](https://github.com/Legilibre/legi.py)

Utilise [knex](https://github.com/tgriesser/knex/) pour exploiter les données d'une base PostgreSQL avec [legi-postgres](https://github.com/Legilibre/legi-postgres) et le standard [unist](https://github.com/syntax-tree/unist) pour représenter les textes sous forme d'arbre, de HTML, ou de markdown.

Par défaut l'API utilisateur utilise un serveur de dev public pour fournir les textes.

Vous pouvez utiliser votre propre base de données en montant votre serveur PostgreSQL avec [legi-postgres](https://github.com/legilibre/legi-postgres)

## Install

```sh
npm install legi
```

## Usage

Promise-based API

```js
const Legi = require("legi");

const legi = new Legi();

// liste des codes disponibles
legi.getCodesList().then(console.log);

// code du travail (~1min)
legi.getCode({ cid: "LEGITEXT000006072050", date: "2012-03-05" }).then(console.log);

// section d'un texte
legi.getSection({ id: "LEGISCTA000006132321", date: "2018-05-03" }).then(console.log);

// conversion en markdown
const markdown = require("legi/src/markdown");
legi
  .getCode({ cid: "LEGITEXT000006069414", date: "2012-03-05" })
  .then(markdown)
  .then(console.log);

// conversion en html
const html = require("legi/src/html");
legi
  .getCode({ cid: "LEGITEXT000006069414", date: "2012-03-05" })
  .then(html)
  .then(console.log);
```

Pour utiliser votre propres serveur PostgreSQL :

```
const legi = new Legi({
  client: "pg",
  connection: {
    host: "127.0.0.1",
    port: 5432,
    user: "user",
    password: "pass",
    database: "legi"
  },
  pool: { min: 0, max: 50 }
});
```

Plus d'exemples dans [./examples](./examples)

### A propos

- [legi.py](https://github.com/Legilibre/legi.py) est un module python qui génère une base sqlite à partir de la base LEGI, normalise et consolide les données.

- [legi-postgres](https://github.com/Legilibre/legi-postgres) convertit cette base dans une base PostgreSQL.

- [legi.js](https://github.com/revolunet/legi.js) permet d'interroger cette base avec une API JavaScript.

## Todo

- gestion dates/versions
- gestion textes type JORF, decrets...

### Related

- https://github.com/Legilibre/legi.py
- https://github.com/Legilibre/Archeo-Lex
- https://github.com/Legilibre/legi-php
- https://github.com/Legilibre/legi-postgres
