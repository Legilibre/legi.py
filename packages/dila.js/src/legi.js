const memoize = require("fast-memoize");
const knexRequire = require("knex");

// default sqlite config
const getKnexConfig = dbPath => ({
  client: "sqlite3",
  useNullAsDefault: true,
  connection: {
    filename: dbPath
  },
  pool: {}
});

const legi = dbPath => {
  const knex = knexRequire(getKnexConfig(dbPath)); //.debug();

  // tasty curry
  const knexify = module => params => module(knex, params);

  return {
    getCode: knexify(require("./getCode")),
    getCodeDates: knexify(require("./getCodeDates")),
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
