const routes = require("express").Router();
const legi = require("../../legi");

/*
 parents
 liens
 versions
*/
routes.get("/code/:code/article/:article", async (req, res) => {
  const article = await legi.getArticle({
    cid: req.params.code,
    id: req.params.article,
    date: "2018-12-01"
  });
  res.json(article);
});

module.exports = routes;
