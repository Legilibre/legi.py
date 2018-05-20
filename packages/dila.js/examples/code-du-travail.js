const Legi = require("../src/Legi");
const markdown = require("../src/markdown");

const legi = new Legi();

// récupères le code du travail
legi
  .getCode({ id: "LEGITEXT000006072050" })
  .then(markdown)
  .then(console.log)
  .catch(console.log);
