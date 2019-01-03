const makeArticle = require("./makeArticle");
const getArticleData = require("./getArticleData");

const getLiens = (knex, { id }) =>
  knex
    .select("src_id", "dst_cid", "dst_id", "dst_titre", "typelien")
    .from("liens")
    .where({ src_id: id })
    .orWhere({ dst_id: id });

const getArticle = async (knex, { id }) => {
  const article = await getArticleData(knex, { id });
  const liens = await getLiens(knex, { id });
  if (!article) {
    return null;
  }
  return makeArticle({
    ...article,
    liens
  });
};

module.exports = getArticle;
