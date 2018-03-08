# legi.js

Une API NodeJS pour requêter une base issue de [legi.py](https://github.com/Legilibre/legi.py).

## Usage

```js
const legi = require('legi');



```

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