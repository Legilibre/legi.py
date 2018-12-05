const routes = require("express").Router();

const find = require("unist-util-find");
var parents = require("unist-util-parents");

// extract basic text structure
const getArticle = (tree, id) =>
  find(parents(tree), node => node.type === "article" && node.data.id === id);

//const getParents = (tree, id) =>

const inputFile = require("../../../../legi.js/2018-12-01.json");

routes.get("/texte/:texteId/article/:id", async (req, res) => {
  res.json(getArticle(inputFile, req.params.id));
});

module.exports = routes;
