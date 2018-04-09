const memoize = require("fast-memoize");
const knexRequire = require("knex");

const defaultKnexConfig = require("./knexfile");

const legi = (dbPath, knexConfig = {}) => {
  const knex = knexRequire({
    ...defaultKnexConfig,
    ...knexConfig
  });

  // console.log(
  //   JSON.stringify(
  //     {
  //       ...defaultKnexConfig,
  //       ...knexConfig
  //     },
  //     null,
  //     2
  //   )
  // );

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
