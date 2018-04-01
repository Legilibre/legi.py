const getCodeVersions = (knex, filters) => {
  return (
    knex
      .clearSelect()
      .clearWhere()
      .clearOrder()
      .select("debut", "fin")
      //.debug()
      .from("sommaires")
      .where(filters)
      .orderBy("debut")
  );
};

module.exports = getCodeVersions;
