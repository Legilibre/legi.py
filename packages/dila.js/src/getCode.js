const extractText = require("./extractText");

const getCodeParams = filters => {
  const isSingleString = typeof filters === "string";
  return isSingleString ? { id: filters } : filters;
};

module.exports = (knex, filters) => extractText(knex, getCodeParams(filters));
