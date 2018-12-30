const getLinks = (knex, id) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select()
    .table("liens")
    .where({ src_id: id });
//.orderBy("typelien");

module.exports = getLinks;
