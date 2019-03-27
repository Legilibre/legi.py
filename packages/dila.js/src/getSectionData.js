const getSectionData = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select("id", "titre_ta AS titre", "commentaire", "parent", "dossier", "cid", "mtime")
    .from("sections")
    .where(filters)
    .first();

module.exports = getSectionData;
