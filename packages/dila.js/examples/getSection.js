const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get single section
dila
  .getSection({
    id: "LEGISCTA000006088039",
    date: "2018-12-01"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
