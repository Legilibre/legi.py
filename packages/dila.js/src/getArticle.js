const getArticleData = require("./getArticleData");
const { cleanData } = require("./utils");
const getLinks = require("./getLinks");

const getArticle = async (knex, filters) => {
  const article = await getArticleData(knex, filters);
  if (!article) {
    return null;
  }
  return {
    type: "article",
    data: cleanData({
      titre: `Article ${article.num}`,
      ...article,
      liens: getLinks(knex, article.id)
    })
  };
};

module.exports = getArticle;
