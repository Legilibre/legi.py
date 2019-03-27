const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get code sommaire
dila
  .getSommaireConteneur({ id: "KALICONT000005635807", date: "2019-01-01", includeArticles: true})
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);

