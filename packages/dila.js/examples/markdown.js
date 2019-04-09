const dila = require("./dila");

const markdown = require("../src/markdown");

// get full code in markdown format
dila
  .getTexte({ id: "LEGITEXT000006070666", date: "2018-12-01" })
  .then(markdown)
  .then(console.log)
  .catch(console.log)
  .then(dila.close);
