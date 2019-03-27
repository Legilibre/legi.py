const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get code structure
dila
  .getTexte({ id: "KALITEXT000030579247", date: "2019-01-01" })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
