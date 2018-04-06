const Legi = require("../src/Legi");

const legi = new Legi();

legi.getCode({ id: "LEGITEXT000006072050", date: "2018-01-01" }).then(tree => {
  console.log(JSON.stringify(tree, null, 2));
  legi.close();
});
