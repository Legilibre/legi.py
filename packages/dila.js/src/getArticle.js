const makeArticle = require("./makeArticle");
const getArticleData = require("./getArticleData");

const getArticle = async (knex, { id }) => {
  const article = await getArticleData(knex, { id });
  if (!article) {
    return null;
  }
  return makeArticle(article);
};

module.exports = getArticle;
