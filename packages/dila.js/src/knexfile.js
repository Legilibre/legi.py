const defaultConfig = {
  client: "pg",
  version: "9.6",
  connection: {
    host: "legi.vps.revolunet.com",
    port: 5444,
    user: "legi",
    password: "legi",
    database: "legi"
  },
  pool: {
    min: 2,
    max: 50
  }
};

module.exports = {
  ...defaultConfig,
  test: defaultConfig
};
