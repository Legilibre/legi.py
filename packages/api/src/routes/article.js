const routes = require("express").Router();
const memoize = require("memoizee");

const getDila = require("../getDila");

const getArticleData = memoize(
  (baseDILA, id) => getDila(baseDILA).getArticle({id}),
  { promise: true }
);
/*
 parents
 liens
 versions
*/
routes.get("/article/:article", async (req, res) => {
  const article = await getArticleData(req.baseDILA, req.params.article);
  res.json(article);
});

module.exports = routes;
