const routes = require("express").Router();
const memoize = require("memoizee");

const getLegi = require("../getLegi");

const getConteneurData = memoize(
  (baseDILA, id, date) => getLegi(baseDILA).getConteneur({id, date}),
  { promise: true }
);

routes.get("/conteneur/:conteneurId", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const conteneur = await getConteneurData(req.baseDILA, req.params.conteneurId, date);
  res.json(conteneur);
});

module.exports = routes;
