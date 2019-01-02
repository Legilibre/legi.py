const routes = require("express").Router();
const memoize = require("memoizee");

const legi = require("../../legi");

const getArticleData = memoize(
  (code, article) =>
    legi.getArticle({
      cid: code,
      id: article,
      date: "2018-12-01"
    }),
  { promise: true }
);
/*
 parents
 liens
 versions
*/
routes.get("/code/:code/article/:article", async (req, res) => {
  const article = await getArticleData(req.params.code, req.params.article);
  res.json(article);
});

module.exports = routes;
