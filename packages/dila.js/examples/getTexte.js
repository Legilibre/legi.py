const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code structure
legi
  .getTexte({ id: "KALITEXT000030579247", date: "2019-01-01" })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
