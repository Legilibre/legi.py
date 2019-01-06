const routes = require("express").Router();

const legi = require("../legi");

routes.get("/codes", async (req, res) => {
  const data = await legi.getCodesList();
  res.json(data);
});

module.exports = routes;
