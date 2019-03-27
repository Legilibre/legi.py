const routes = require("express").Router();

const getLegi = require("../getLegi");

routes.get("/conteneurs", async (req, res) => {
  const filters = Object.keys(req.query)
    .filter(key => ["nature", "etat"].includes(key))
    .reduce((obj, key) => ({...obj, [key]: req.query[key]}), {});
  const items = await getLegi(req.baseDILA).getConteneursList(filters);
  res.json(items);
});

module.exports = routes;
