const memoize = require("fast-memoize");
const knexRequire = require("knex");

// default sqlite config
const getDefaultKnexConfig = dbPath => ({
  // client: "sqlite3",
  // useNullAsDefault: true,
  // connection: {
  //   filename: dbPath
  // },
  // pool: {}
  client: "pg",
  version: "9.6",
  connection: {
    host: "127.0.0.1",
    port: 5444,
    user: "user",
    password: "pass",
    database: "legi"
  }
});

const legi = (dbPath, knexConfig = {}) => {
  const knex = knexRequire({
    ...getDefaultKnexConfig(dbPath),
    ...knexConfig
  });

  // tasty curry
  const knexify = module => params => module(knex, params);

  return {
    getCode: knexify(require("./getCode")),
    getCodeVersions: knexify(require("./getCodeVersions")),
    getCodesList: knexify(require("./getCodesList")),
    getJORF: knexify(require("./getJORF")),
    getSection: knexify(require("./getSection")),
    close: knex.destroy,
    knex
  };
};

class Legi {
  constructor(dbPath = "./legi.sqlite") {
    return legi(dbPath);
  }
}

module.exports = Legi;
