const legi = require("./legi");

const markdown = require("../src/markdown");

// get full code in markdown format
legi
  .getCode({ cid: "LEGITEXT000006070666", date: "2018-12-01" })
  .then(markdown)
  .then(console.log)
  .catch(console.log)
  .then(legi.close);
