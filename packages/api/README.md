# legi-api

API http pour interroger les textes issus de la base LEGI.

Le format par défaut est le JSON, avec un structure d'arbre [unist](https://github.com/syntax-tree/unist)

NB: vous devez disposer d'une base de données `legi-postgres`

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

## Related

- https://github.com/revolunet/legi.js
- https://github.com/Legilibre/legi-postgres
- https://github.com/Legilibre/legi.py
