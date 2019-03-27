const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get code sommaire
dila
  .getCodesList()
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
