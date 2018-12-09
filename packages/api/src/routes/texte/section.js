const routes = require("express").Router();

const find = require("unist-util-find");

// extract basic text structure
const getSection = (tree, id) =>
  find(tree, node => node.type === "section" && node.data.id === id);

routes.get("/texte/:texte/section/:section", async (req, res) => {
  const data = require(`../../../../legi.js/codes/${req.params.texte}.json`);
  res.json(getSection(data, req.params.section));
});

module.exports = routes;
