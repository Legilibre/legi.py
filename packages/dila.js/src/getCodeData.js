const getCodeData = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select("cid", "titre", "titrefull", "date_publi")
    .from("textes_versions")
    .where(filters)
    .orderBy("date_publi", "desc")
    .first()
    .catch(console.log);

module.exports = getCodeData;
