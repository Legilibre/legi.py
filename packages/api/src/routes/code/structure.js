const routes = require("express").Router();
const legi = require("../../legi");

const map = require("unist-util-map");

// extract basic text structure
const getStructure = tree =>
  map(tree, node => ({
    children: node.children,
    type: node.type,
    id: node.data.id,
    titre_ta: node.data.titre_ta || node.data.titre
  }));

routes.get("/code/:code/structure", async (req, res) => {
  const data = await legi.getSommaire({
    cid: req.params.code,
    date: "2018-12-01"
  });
  res.json(getStructure(data));
});

module.exports = routes;
