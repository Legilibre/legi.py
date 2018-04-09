const getCodeVersions = (knex, filters) => {
  let filters2 = { ...filters };
  if (typeof filters === "string") {
    filters2 = { cid: filters };
  }
  return (
    knex
      .clearSelect()
      .clearWhere()
      .clearOrder()
      //.distinct("debut", "fin")
      .select()
      .from("sommaires")
      .where(filters2)
      //.groupBy("debut", "fin", "cid")
      .orderBy("debut", "titre")
  );
};

module.exports = getCodeVersions;
