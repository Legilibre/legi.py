const getTetierData = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select("id", "titre_tm", "niv", "conteneur_id")
    .from("tetiers")
    .where(filters)
    .first()
    .catch(console.log);

module.exports = getTetierData;
