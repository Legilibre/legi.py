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
const JSONlog = data => console.log(JSON.stringify(data, null, 2)) || data;

const cleanTitle = str =>
  (str &&
    str
      .trim()
      .replace(/&#13;\s*/g, "")
      .replace(/\n/g, " ")
      .replace(/\s\s+/g, " ")
      .replace(/\s+\.\s*$/g, " ")
      .trim()
      // existing full whitespace patterns
      .replace(/^<br\/><br\/><br\/><p><br\sclear="none"\/><\/p>$/, "")
      .replace(/^<p><br\sclear="none"\/><\/p>$/, "")
      // html extra br trim
      .replace(/^((\s*<br\/>\s*)*)*/, "")
      .replace(/((\s*<br\/>\s*)*)*$/, "")) ||
  "";

const cleanData = (
  obj,
  titres = ["titre", "titrefull", "nota", "commentaire", "bloc_textuel"]
) =>
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

const sortByKey = key => (a, b) => {
  const getValue = (obj, key) => {
    if (key.indexOf(".") > -1) {
      const [first, second] = key.split(".");
      return obj[first][second];
    } else {
      return obj[key];
    }
  };
  if (getValue(a, key) < getValue(b, key)) return -1;
  if (getValue(a, key) > getValue(b, key)) return 1;
  return 0;
};

const getItemType = item => {
  if (item.id.substring(4, 8) == "SCTA") {
    return "section";
  } else if (item.id.substring(4, 8) == "TEXT") {
    return "texte";
  } else if (item.id.substring(4, 8) == "ARTI") {
    return "article";
  } else if (item.id.substring(4, 6) == "TM") {
    return "tetier";
  }
};
const canContainChildren = item => ["section", "texte", "tetier"].includes(getItemType(item));

// transform flat rows to hierarchical tree
const makeAst = (rows, parent = null) => {
  return rows
    .filter(row => row.data.parent === parent)
    .sort(sortByKey("data.position"))
    .map(row => ({
      ...row,
      // add children nodes for sections
      children: (canContainChildren(row.data) && makeAst(rows, row.data.id)) || undefined
    }));
};

module.exports = {
  serial,
  read,
  write,
  serialExec,
  makeAst,
  range,
  repeat,
  cleanTitle,
  cleanData,
  JSONread,
  JSONlog,
  sortByKey,
  getItemType,
  canContainChildren
};
