const routes = require("express").Router();
const memoize = require("memoizee");

const getDila = require("../getDila");

const getConteneurData = memoize(
  (baseDILA, id, date) => getDila(baseDILA).getConteneur({id, date}),
  { promise: true }
);

routes.get("/conteneur/:conteneurId", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const conteneur = await getConteneurData(req.baseDILA, req.params.conteneurId, date);
  res.json(conteneur);
});

module.exports = routes;
