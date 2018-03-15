const express = require("express");
const memoize = require("fast-memoize");
const Legi = require("legi");

const app = express();

const legi = new Legi();

const memoizedGetCode = memoize(legi.getCode);
const memoizedGetJORF = memoize(legi.getJORF);
const memoizedGetSection = memoize(legi.getSection);

const today = () => new Date().toISOString().substring(0, 10);

app.get("/texte/:id", async (req, res) => {
  const id = req.params.id;
  const date = req.query.date || today();
  const format = req.query.format;
  let texte;
  if (id.match(/^LEGISCTA/)) {
    texte = await memoizedGetSection({ parent: id, date });
  } else if (id.match(/^JORFTEXT/)) {
    texte = await memoizedGetJORF(id);
  } else {
    texte = await memoizedGetCode({ id, date });
  }
  res.json(texte);
});

const PORT = process.env.PORT || 3005;

app.listen(PORT, () => {
  console.log(`listening on http://127.0.0.1:${PORT}`);
});
