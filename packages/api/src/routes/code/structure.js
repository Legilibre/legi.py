const routes = require("express").Router();
const memoize = require("memoizee");
const map = require("unist-util-map");

const legi = require("../../legi");

// extract basic text structure
const getStructure = tree =>
  map(tree, node => ({
    children: node.children,
    type: node.type,
    id: node.data && node.data.id,
    titre_ta: (node.data && (node.data.titre_ta || node.data.titre)) || ""
  }));

const getSommaireData = memoize(
  code =>
    legi.getSommaire({
      cid: code,
      date: "2018-12-01"
    }),
  { promise: true }
);

routes.get("/code/:code/structure", async (req, res) => {
  const data = await getSommaireData(req.params.code);
  res.json(getStructure(data));
});

module.exports = routes;
