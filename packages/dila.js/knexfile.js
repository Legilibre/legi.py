module.exports = {
  postgres: {
    client: "pg",
    connection: "postgresql://postgres:test@127.0.0.1:5434/legi",
    searchPath: ["knex", "public"],
    pool: { min: 2, max: 20 }
  },
  sqlite: {
    client: "sqlite3",
    connection: {
      filename: "../legilibre/legi.py-docker/tarballs/legilibre.sqlite"
    }
  }
};
