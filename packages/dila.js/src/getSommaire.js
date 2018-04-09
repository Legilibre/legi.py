const getSommaire = (knex, filters) => {
  const sommaireFilters = {
    ...filters
  };
  delete sommaireFilters.date; // not a valid sql field
  delete sommaireFilters.id; // not a valid sql field
  if (filters.id) {
    sommaireFilters.cid = filters.id;
  }
  return (
    knex
      // .debug()
      .clearSelect()
      .clearWhere()
      .clearOrder()
      .select()
      .table("sommaires")
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
