const getCodeVersions = (knex, filters) => {
  let filters2 = { ...filters };
  if (typeof filters === "string") {
    filters2 = { cid: filters };
  }
  return knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select("debut")
    .distinct()
    .from("sommaires")
    .where(filters2)
    .orderBy("debut");
};

module.exports = getCodeVersions;
