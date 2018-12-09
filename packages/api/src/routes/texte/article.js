const routes = require("express").Router();

const find = require("unist-util-find");
var parents = require("unist-util-parents");

const getParents = node => {
  const parents = [];
  while ((node = node.parent)) {
    if (node.data && node.data.id) {
      parents.push({
        id: node.data.id,
        titre_ta: node.data.titre_ta
      });
    }
  }
  parents.reverse();
  return parents;
};

// extract basic text structure
const getArticle = (tree, id) => {
  const article = find(
    parents(tree),
    node => node.type === "article" && node.data.id === id
  );
  if (article.parent) {
    article.parents = getParents(article);
  }
  return article;
};

routes.get("/texte/:texte/article/:article", async (req, res) => {
  const data = require(`../../../../legi.js/codes/${req.params.texte}.json`);
  res.json(getArticle(data, req.params.article));
});

module.exports = routes;
