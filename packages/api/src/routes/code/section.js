const routes = require("express").Router();
const memoize = require("memoizee");

const legi = require("../../legi");

const getSectionData = memoize(
  (code, section) =>
    legi
      .getSection({
        cid: code,
        id: section,
        date: "2018-12-01"
      })
      .then(res => {
        console.log("res", res);
        return res;
      }),
  { promise: true }
);

routes.get("/code/:code/section/:section", async (req, res) => {
  const section = await getSectionData(req.params.code, req.params.section);
  res.json(section);
});

module.exports = routes;
