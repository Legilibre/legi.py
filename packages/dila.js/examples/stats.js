const fs = require("fs");
const visit = require("unist-util-visit");

const Legi = require("../src/Legi");

const legi = new Legi();
const { range, JSONread } = require("../src/utils");

// utilise les données issues de export-json.js

const getPath = (id = "LEGITEXT000006072050", date = "2018-01-01") =>
  `./history/code-du-travail/${id}-${date}.json`;

const filterAllBy = (tree, predicate) => {
  const results = [];
  visit(tree, visitor);
  function visitor(node) {
    if (predicate(node)) results.push(node);
  }
  return results;
};

// volumétrie par an
// utilise un export crée précédemment pour + de rapidité (todo)
const getYearStats = year => {
  const content = JSONread(getPath("LEGITEXT000006072050", `${year}-01-01`));
  return {
    year,
    sections: filterAllBy(content, n => n.type === "section").length,
    articles: filterAllBy(content, n => n.type === "article").length
  };
};

// stats par an sur le code du travail
const results = range(1977, 2019).map(getYearStats);

//console.log(JSON.stringify(results, null, 2));

results.forEach(d => {
  console.log(`${d.year};${d.sections};${d.articles}`);
});
