const express = require("express");
const cors = require("cors");

const getLegi = require("./getLegi");
const pkg = require("../package.json");

const app = express();
app.use(cors());

app.use(
  "/v1/base/:baseDILA",
  function(req, res, next) {
    req.baseDILA = req.params.baseDILA;
    next();
  },
  require("./routes/texteStructure"),
  require("./routes/conteneurStructure"),
  require("./routes/section"),
  require("./routes/article"),
  require("./routes/tetier"),
  require("./routes/codes"),
  require("./routes/conteneur"),
  require("./routes/conteneurs")
);
// TODO : can't we use /routes/* ?

app.get("/", (req, res) => res.send({ version: pkg.version, name: pkg.name }));

const PORT = process.env.PORT || 3005;
const HOST = process.env.NODE_ENV == 'production' ? '0.0.0.0' : '127.0.0.1';

app.listen(PORT, HOST, () => {
  console.log(`listening on http://${HOST}:${PORT}`);
});
