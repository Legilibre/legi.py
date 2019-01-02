const Legi = require("../src/Legi");
const { JSONlog } = require("../src/utils");
const html = require("../src/html");
const markdown = require("../src/markdown");

const legi = new Legi({
  client: "pg",
  connection: {
    host: "vps.revolunet.com",
    port: 5444,
    user: "legi",
    password: "legi",
    database: "legi"
  }
});

/*
 code/xxx                       OK
 code/xxx/article/xxx           OK
 code/xxx/article/xxx/liens     NOK
 code/xxx/article/xxx/versions  NOK
 code/xxx/section/xxx           OK
*/

// get single section
legi
  .getSection({
    id: "LEGISCTA000006088039"
  })
  .then(JSONlog)
  .catch(console.log);

// get single article
legi
  .getArticle({
    id: "LEGIARTI000006398351"
  })
  .then(JSONlog)
  .catch(console.log);

// get full code in html format
legi
  .getCode({ cid: "LEGITEXT000006070666", date: "2018-12-01" })
  .then(html)
  .then(console.log)
  .catch(console.log)
  .then(() => legi.close());

// get code sommaire
legi
  .getSommaire({ cid: "LEGITEXT000006072050", date: "2018-12-01" })
  .then(console.log)
  .catch(console.log)
  .then(() => legi.close());
