const routes = require("express").Router();
const memoize = require("memoizee");
const map = require("unist-util-map");

const getLegi = require("../getLegi");

// extract basic text structure
const getStructure = tree =>
  map(tree, node => ({
    children: node.children,
    type: node.type,
    id: node.data && node.data.id,
    titre: node.data && node.data.titre,
    titrefull: node.data && node.data.titrefull
  }));

const getSommaireData = memoize(
  (baseDILA, id, date) => getLegi(baseDILA).getSommaireTexte({id, date}),
  { promise: true }
);

routes.get("/texte/:texte/structure", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const data = await getSommaireData(req.baseDILA, req.params.texte, date);
  res.json(getStructure(data));
});

module.exports = routes;
