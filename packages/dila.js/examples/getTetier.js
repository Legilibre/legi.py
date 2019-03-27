const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get single article
dila
  .getTetier({
    id: "KALITM000030594537-0"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
