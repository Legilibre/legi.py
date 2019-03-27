const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code sommaire
legi
  .getSommaireConteneur({ id: "KALICONT000005635807", date: "2019-01-01", includeArticles: true})
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);

