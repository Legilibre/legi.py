const fs = require("fs");
const visit = require("unist-util-visit");

const Legi = require("../src/Legi");

const legi = new Legi();
const { range, JSONread } = require("../src/utils");

const buildYears = async id => buildDates(id, range(1977, 2019).map(y => `${y}-01-01`));

const getPath = (id = "LEGITEXT000006072050", date = "2018-01-01") =>
  `./history/code-du-travail/${id}-${date}.json`;

const count = tree => {};

const filterAllBy = (tree, predicate) => {
  const results = [];
  visit(tree, visitor);
  function visitor(node) {
    if (predicate(node)) results.push(node);
  }
  return results;
};

// volumétrie par an
const getYearStats = year => {
  const content = JSONread(getPath("LEGITEXT000006072050", `${year}-01-01`));
  return {
    year,
    sections: filterAllBy(content, n => n.type === "section").length,
    articles: filterAllBy(content, n => n.type === "article").length
  };
};

const results = range(1977, 2019).map(getYearStats);

//console.log(JSON.stringify(results, null, 2));

results.forEach(d => {
  console.log(`${d.year};${d.sections};${d.articles}`);
});
