const getCodeDates = async (knex, { id }) => {
  const versions = await knex
    .select("debut", "fin")
    //.debug()
    .table("sommaires")
    .where("cid", id)
    .orderBy("debut");

  const allVersions = Array.from(versions.reduce((a, c) => a.add(c.debut).add(c.fin), new Set()));

  allVersions.sort();

  return allVersions;
};

module.exports = getCodeDates;
