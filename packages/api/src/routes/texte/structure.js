const routes = require("express").Router();

const remove = require("unist-util-remove");
const map = require("unist-util-map");

// extract basic text structure
const getStructure = tree =>
  map(tree, node => ({
    children: node.children,
    type: node.type,
    id: node.data.id,
    titre_ta: node.data.titre_ta || node.data.titre
  }));

const inputFile = require("../../../../legi.js/2018-12-01.json");

routes.get("/texte/:id/structure", async (req, res) => {
  res.json(getStructure(inputFile));
});

module.exports = routes;
