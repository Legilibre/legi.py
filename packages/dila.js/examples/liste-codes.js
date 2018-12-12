const Legi = require("../src/Legi");

const { JSONlog } = require("../src/utils");

//const legi = new Legi();

const legi = new Legi({
  client: "sqlite3",
  connection: {
    filename: "legilibre.sqlite"
  }
});

legi
  .getCodesList()
  .then(list => list.map(code => ({ id: code.id, titre: code.titrefull })))
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
