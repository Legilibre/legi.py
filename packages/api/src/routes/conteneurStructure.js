const routes = require("express").Router();
const memoize = require("memoizee");
const map = require("unist-util-map");

const getDila = require("../getDila");

// extract basic text structure
const getStructure = tree =>
  map(tree, node => ({
    children: node.children,
    type: node.type,
    id: node.data && node.data.id,
    titre: node.data && node.data.titre
  }));

const getSommaireData = memoize(
  (baseDILA, id, date, includeArticles) => (
    getDila(baseDILA).getSommaireConteneur({id, date, includeArticles})
  ),
  { promise: true }
);

routes.get("/conteneur/:conteneurId/structure", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const includeArticles = req.query.includeArticles === 'true' || false;
  const data = await getSommaireData(req.baseDILA, req.params.conteneurId, date, includeArticles);
  res.json(getStructure(data));
});

module.exports = routes;
