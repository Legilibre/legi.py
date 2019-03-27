const routes = require("express").Router();

const getDila = require("../getDila");

routes.get("/codes", async (req, res) => {
  const data = await getDila(req.baseDILA).getCodesList();
  res.json(data);
});

module.exports = routes;
