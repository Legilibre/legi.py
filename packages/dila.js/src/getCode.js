const extractVersion = require("./extractVersion");

const getCodeParams = params => {
  const isSingleString = params.length === 1 && typeof params[0] === "string";
  return isSingleString ? { id: params[0] } : params[0];
};

module.exports = (knex, ...args) => extractVersion(knex, getCodeParams(args));
