const getArticle = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select()
    .from("articles")
    .where(filters)
    .first();

module.exports = getArticle;
