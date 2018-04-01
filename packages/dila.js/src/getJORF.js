const getJORF = async (knex, id) => {
  const version = await knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .table("textes_versions")
    .where({ cid: id })
    .first();
  const articles = await knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .table("articles")
    .where({ cid: id })
    .orderBy("num");

  const children = articles.map(a => ({
    id: a.id,
    type: "article",
    data: a,
    children: []
  }));

  return {
    id,
    type: "texte",
    data: version,
    children
  };
};

module.exports = getJORF;
