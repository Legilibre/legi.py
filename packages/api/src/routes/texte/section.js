const routes = require("express").Router();

const find = require("unist-util-find");

// extract basic text structure
const getSection = (tree, id) =>
  find(tree, node => node.type === "section" && node.data.id === id);

const inputFile = require("../../../../legi.js/2018-12-01.json");

routes.get("/texte/:texteId/section/:id", async (req, res) => {
  res.json(getSection(inputFile, req.params.id));
});

module.exports = routes;
