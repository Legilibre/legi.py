# dila2sql - API

API HTTP pour interroger les bases générées par `dila2sql` : LEGI, KALI, etc...

Le format par défaut est le JSON, avec un structure d'arbre [unist](https://github.com/syntax-tree/unist)

## Local development setup

If you want to make local changes to `dila.js` and see their impact in the API, you can update the require line in `src/getDila.js` with:

```js
const Dila = require("../../dila.js");
```

You should also install `nodemon` so that the server watches file changes and reloads automatically : `npm install -g nodemon`.

You can now start the server with this command to see all the logs:

```
yarn dev
```

## Usage

- `/codes` : récupérer la liste des codes disponibles
- `/code/[ID]` : récupérer un texte complet
  - `?date=2010-01-01` : état du texte pour une date donnée [TODO]
  - `?format=json|markdown|html` : récupérer dans le format donné [TODO]

## Exemple

- `/code/LEGITEXT000006069414` : code de la propriété intellectuelle
- `/code/LEGITEXT000006069414?date=2016-01-01` : code de la propriété intellectuelle au 1/1/2016
- `/code/LEGITEXT000006069414?date=2016-01-01&format=html` : code de la P.I. au 1/1/2016 en HTML
- `/code/JORFTEXT000000465978` : texte du journal officiel
- `/code/LEGISCTA000006132321` : une section du code du travail
