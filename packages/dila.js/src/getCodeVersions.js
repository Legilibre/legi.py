const getCodeVersions = (knex, filters) => {
  return (
    knex
      .select("debut", "fin")
      //.debug()
      .table("sommaires")
      .where(filters)
      .orderBy("debut")
  );
};

module.exports = getCodeVersions;
