const getSectionData = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select()
    .from("sections")
    .where(filters)
    .first();

module.exports = getSectionData;
