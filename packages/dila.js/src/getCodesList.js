const getCodesList = knex => knex.table("textes_versions").where({ nature: "CODE" });

module.exports = getCodesList;
