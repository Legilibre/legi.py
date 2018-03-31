const getSommaire = (knex, filters) => {
  const sommaireFilters = {
    ...filters
  };
  delete sommaireFilters.date; // not a valid sql field

  return (
    knex
      .table("sommaires")
      //.debug()
      .where(sommaireFilters)
      .andWhere("debut", "<=", filters.date)
      .andWhere(function() {
        return this.where("fin", ">", filters.date)
          .orWhere("fin", "2999-01-01")
          .orWhere("etat", "VIGUEUR");
      })
      .orderBy("position")
      .catch(console.log)
  );
};

module.exports = getSommaire;
