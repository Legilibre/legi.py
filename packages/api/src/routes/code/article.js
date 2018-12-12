const routes = require("express").Router();
const find = require("unist-util-find");
const parents = require("unist-util-parents");

const getParentSections = require("../../getParentSections");

// extract basic text structure
const getArticle = (tree, id) => {
  const article = find(
    parents(tree),
    node => node.type === "article" && node.data.id === id
  );
  if (article.parent) {
    article.parents = getParentSections(article);
  }
  return article;
};

routes.get("/code/:code/article/:article", async (req, res) => {
  const data = require(`../../../codes/${req.params.code}.json`);
  res.json(getArticle(data, req.params.article));
});

module.exports = routes;
