const getCodesList = knex =>
  knex
    .table("textes_versions")
    .where({ nature: "CODE" })
    .orderBy("titre");

module.exports = getCodesList;
