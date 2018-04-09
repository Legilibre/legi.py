const defaultConfig = {
  client: "pg",
  version: "9.6",
  connection: {
    host: "127.0.0.1",
    port: 5444,
    user: "user",
    password: "pass",
    database: "legi"
  }
};

module.exports = {
  ...defaultConfig,
  sqlite: {
    client: "sqlite3",
    useNullAsDefault: true,
    connection: {
      filename: "legi.sqlite"
    },
    pool: {}
  }
};
