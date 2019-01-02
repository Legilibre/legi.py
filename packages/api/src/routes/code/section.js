const routes = require("express").Router();
const legi = require("../../legi");

routes.get("/code/:code/section/:section", async (req, res) => {
  const section = await legi.getSection({
    cid: req.params.code,
    id: req.params.section,
    date: "2018-12-01"
  });
  res.json(section);
});

module.exports = routes;
