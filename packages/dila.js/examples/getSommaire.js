const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code sommaire
legi
  .getSommaire({ cid: "LEGITEXT000006072050", date: "2018-12-01" })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
