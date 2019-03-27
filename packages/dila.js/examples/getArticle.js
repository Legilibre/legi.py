const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get single article
legi
  .getArticle({
    id: "LEGIARTI000006398351"
  })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);

