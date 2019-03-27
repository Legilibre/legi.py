const dila = require("./dila");

const html = require("../src/html");

// get full code in html format
dila
  .getCode({ cid: "LEGITEXT000006070666", date: "2018-12-01" })
  .then(html)
  .then(console.log)
  .catch(console.log)
  .then(dila.close);
