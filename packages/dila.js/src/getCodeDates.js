const getCodeVersions = require("./getCodeVersions");

const getCodeDates = async (knex, filters) => {
  const versions = await getCodeVersions(knex, filters);
  const allVersions = Array.from(versions.reduce((a, c) => a.add(c.debut).add(c.fin), new Set()));
  allVersions.sort();
  return allVersions;
};

module.exports = getCodeDates;
