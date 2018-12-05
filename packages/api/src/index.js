const express = require("express");
const cors = require("cors");

// const Legi = require("legi");
// const toMarkdown = require("legi/src/markdown");
// const toHtml = require("legi/src/html");

const pkg = require("../package.json");

const app = express();
app.use(cors());
// const legi = new Legi({
//   client: "sqlite3",
//   connection: {
//     filename: "legilibre.sqlite"
//   }
// });

// const inputFile = require("../legi.js/2018-12-01.json");

// const today = () => new Date().toISOString().substring(0, 10);

// const remove = require("unist-util-remove");
// const map = require("unist-util-map");

// // extract basic text structure
// const getStructure = tree =>
//   map(remove(tree, "article"), node => ({
//     children: node.children,
//     type: node.type,
//     id: node.data.id,
//     titre_ta: node.data.titre_ta
//   }));

app.use("/", require("./routes/texte/structure"));
app.use("/", require("./routes/texte/section"));
app.use("/", require("./routes/texte/article"));

// app.get("/texte/:id", async (req, res) => {
//   const id = req.params.id;
//   const date = req.query.date || today();
//   const format = req.query.format;
//   let tree;
//   if (id.match(/^LEGISCTA/)) {
//     tree = await memoizedGetSection({ parent: id, date });
//   } else if (id.match(/^JORFTEXT/)) {
//     tree = await memoizedGetJORF(id);
//   } else {
//     tree = await memoizedGetCode({ id, date });
//   }
//   console.log("tree", tree);
//   if (format === "markdown") {
//     res.send(await toMarkdown(tree));
//   } else if (format === "html") {
//     res.send(await toHtml(tree));
//   } else {
//     res.json(tree);
//   }
// });

app.get("/", (req, res) => res.send({ version: pkg.version, name: pkg.name }));

const PORT = process.env.PORT || 3005;

app.listen(PORT, () => {
  console.log(`listening on http://127.0.0.1:${PORT}`);
});
