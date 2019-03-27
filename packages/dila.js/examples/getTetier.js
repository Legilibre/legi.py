const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get single article
legi
  .getTetier({
    id: "KALITM000030594537-0"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
