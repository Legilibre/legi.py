const knexRequire = require("knex");

const defaultKnexConfig = require("./knexfile");

const legi = (knexConfig = {}) => {
  const knex = knexRequire({
    ...defaultKnexConfig,
    ...knexConfig
  });

  // tasty curry
  const knexify = module => params => module(knex, params);

  // the public API methods handlers will receive current knex connection as 1st arg
  return {
    getCode: knexify(require("./getCode")),
    getCodesList: knexify(require("./getCodesList")),
    getArticle: knexify(require("./getArticle")),
    getSection: knexify(require("./getSection")),
    getSommaire: knexify(require("./getSommaire")),
    close: () => knex && knex.destroy(),
    knex
  };
};

class Legi {
  constructor(knexConfig) {
    return legi(knexConfig);
  }
}

module.exports = Legi;
