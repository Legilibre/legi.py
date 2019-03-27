const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get code sommaire
dila
  .getSommaireTexte({ id: "KALITEXT000030579247", date: "2018-12-01" })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
