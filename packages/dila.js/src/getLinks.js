const getLinks = (knex, id) =>
  knex
    .table("liens")
    .where({ src_id: id })
    .orderBy("typelien");

module.exports = getLinks;
