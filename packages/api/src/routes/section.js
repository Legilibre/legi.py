const routes = require("express").Router();
const memoize = require("memoizee");

const getLegi = require("../getLegi");

const getSectionData = memoize(
  (baseDILA, id, date) => getLegi(baseDILA).getSection({id, date}),
  { promise: true }
);

routes.get("/section/:section", async (req, res) => {
  const date = new Date().toISOString().slice(0, 10);
  const section = await getSectionData(req.baseDILA, req.params.section, date);
  res.json(section);
});

module.exports = routes;
