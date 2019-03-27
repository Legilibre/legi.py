const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code sommaire
legi
  .getCodesList()
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
