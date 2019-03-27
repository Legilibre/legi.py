const getConteneursList = (knex, userFilters = {}) => {
  const defaultFilters = {
    etat: ["VIGUEUR", "VIGUEUR_ETEN", "VIGUEUR_NON_ETEN"]
  };
  const whitelistedFilters = Object.keys(userFilters)
    .filter(key => ["nature", "etat"].includes(key))
    .reduce((obj, key) => ({ ...obj, [key]: userFilters[key] }), {});

  const filters = { ...defaultFilters, ...whitelistedFilters };

  let query = knex.table("conteneurs");
  if (filters.etat) {
    if (filters.etat instanceof Array) query = query.whereIn("etat", filters.etat);
    else query = query.where("etat", filters.etat);
  }
  if (filters.nature) {
    if (filters.nature instanceof Array) query = query.whereIn("nature", filters.nature);
    else query = query.where("nature", filters.nature);
  }
  return query.orderBy("date_publi", "desc");
};

module.exports = getConteneursList;
