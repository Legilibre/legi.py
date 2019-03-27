const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code sommaire
legi
  .getSommaireTexte({ id: "KALITEXT000030579247", date: "2018-12-01" })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
