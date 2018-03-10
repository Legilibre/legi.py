# legi.js

API NodeJS *Promise-based* pour requêter une base issue de [legi.py](https://github.com/Legilibre/legi.py)

Utilise [knex.js](https://github.com/tgriesser/knex/) et le standard [unist](https://github.com/syntax-tree/unist) pour représenter les textes sous forme d'arbre.


## Usage

```js
const Legi = require('legi');

const legi = new Legi('/path/to/legi.sqlite');

// liste des codes disponibles (105)
const textes = await legi.getCodesList();

// version à date du jour
const codeDuTravail = await legi.getCode("LEGITEXT000006072050")

// version à une date donnée
const codeDesMedailles = await legi.getCode({ id: "LEGITEXT000006070666", date: "2012-03-05" })

// liste des versions d'un texte
const versionsDispos = await legi.getCodeDates("LEGITEXT000006072050");
```

Plus d'exemples dans [./examples.js](./examples.js)

### A propos de legi.py

legi.py est un module python qui génère une base sqlite à partir de la base LEGI, normalise et consolide les données. [plus d'infos ici](https://github.com/Legilibre/legi.py)

Une image docker pour builder et maintenir ce fichier soi-même est dispo ici : [legi.py-docker](https://github.com/revolunet/legi.py-docker)

### Utiliser Postgres

Convertir la base legilibre.sqlite dans Postgres pour de meilleures performances

⚠️ Utiliser [pgloader](https://github.com/dimitri/pgloader) avec le paramètre `--cast "type day to varchar"`

```sh
# lancer pgloader en local
pgloader --cast "type day to varchar" legilibre.sqlite postgresql://postgres:test@127.0.0.1:5433/legi
```