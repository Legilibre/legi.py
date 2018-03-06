# legi.js

### convertir la DB en Postgres

Avec [pgloader](https://github.com/dimitri/pgloader)

```sh
# lancer PostgreSQL
docker run -v $PWD/data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=test -p 5433:5432 -d postgres

# lancer la version
pgloader --cast "type day to varchar" ../legilibre/legi.py-docker/tarballs/legilibre.sqlite postgresql://postgres:test@127.0.0.1:5434/legi

```