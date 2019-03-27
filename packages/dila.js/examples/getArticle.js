const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get single article
dila
  .getArticle({
    id: "LEGIARTI000006398351"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);

