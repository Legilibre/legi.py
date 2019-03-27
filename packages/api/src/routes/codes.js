const routes = require("express").Router();

const getLegi = require("../getLegi");

routes.get("/codes", async (req, res) => {
  const data = await getLegi(req.baseDILA).getCodesList();
  res.json(data);
});

module.exports = routes;
