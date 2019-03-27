const routes = require("express").Router();
const memoize = require("memoizee");

const getLegi = require("../getLegi");

const getTetierData = memoize(
  (baseDILA, id, date) => getLegi(baseDILA).getTetier({id, date}),
  { promise: true }
);

/*
 parents
 liens
 versions
*/
routes.get("/tetier/:id", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const tetier = await getTetierData(req.baseDILA, req.params.id, date);
  res.json(tetier);
});

module.exports = routes;
