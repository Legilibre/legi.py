const getArticle = (knex, filters) =>
  knex
    .select("*")
    .from("articles")
    .where(filters)
    .first();

module.exports = getArticle;
