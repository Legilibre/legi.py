const express = require("express");
const cors = require("cors");

const pkg = require("../package.json");

const app = express();
app.use(cors());

app.use("/", require("./routes/code/structure"));
app.use("/", require("./routes/code/section"));
app.use("/", require("./routes/code/article"));

app.get("/", (req, res) => res.send({ version: pkg.version, name: pkg.name }));

const PORT = process.env.PORT || 3005;

app.listen(PORT, () => {
  console.log(`listening on http://127.0.0.1:${PORT}`);
});
