const fs = require("fs");

// 1-1 promise
const serial = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c.then(cur => [...res, cur])),
    Promise.resolve([])
  );

// 1-1 promise callable
const serialExec = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c().then(cur => [...res, cur])),
    Promise.resolve([])
  );

const repeat = (s, times = 5) =>
  Array.from({ length: times })
    .fill(s)
    .join("");

const logSections = (node, d = 0) => {
  node.children &&
    node.children.forEach(n => {
      if (n.titre.match(/^Article.*/)) {
        console.log(repeat("  ", d), n.titre);
        n.bloc_textuel && console.log(repeat("  ", d + 1), n.bloc_textuel, "\n\n");
      } else {
        console.log(repeat("  ", d), n.titre);
        logSections(n, d + 1);
      }
    });
};

const range = (start, end) => Array.from({ length: end - start }, (k, v) => start + v);

const read = path => fs.readFileSync(path).toString();
const write = (dst, content) => fs.writeFileSync(dst, JSON.stringify(content, null, 2));

const JSONread = path => JSON.parse(read(path));
const JSONlog = data => console.log(JSON.stringify(data, null, 2)) && data;

const cleanTitle = str =>
  (str &&
    str
      .trim()
      .replace(/&#13;/g, "")
      .replace(/\n/g, " ")
      .replace(/\s\s+/g, " ")
      .replace(/\s+\.\s*$/g, " ")
      .trim()) ||
  "";

const cleanData = (obj, titres = ["titre", "titrefull", "titre_ta"]) =>
  (obj && {
    ...Object.keys(obj).reduce(
      (o, k) => ({
        ...o,
        [k]: titres.indexOf(k) > -1 ? cleanTitle(obj[k]) : obj[k]
      }),
      {}
    )
  }) ||
  {};

module.exports = {
  serial,
  read,
  write,
  serialExec,
  range,
  repeat,
  cleanTitle,
  cleanData,
  JSONread,
  JSONlog
};
