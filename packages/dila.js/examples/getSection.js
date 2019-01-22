const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get single section
legi
  .getSection({
    id: "LEGISCTA000006088039",
    date: "2018-12-01"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
