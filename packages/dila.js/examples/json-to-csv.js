const parents = require("unist-util-parents");
const { selectAll } = require("unist-util-select");

// extract basic text structure
const getArticles = tree =>
  selectAll("article", parents(tree)).map(article => ({
    ...article,
    parents: getParentSections(article)
  }));

const getParentSections = (node, chain = []) => {
  if (node.parent && node.parent.type === "section") {
    return getParentSections(
      node.parent,
      (chain = [
        {
          titre_ta: node.parent.data.titre_ta,
          id: node.parent.data.id
        },
        ...chain
      ])
    );
  }
  return chain;
};

// use file built with examples/export-json.js
if (require.main === module) {
  const tree = require("../2018-12-01.json");
  const csv = getArticles(tree).map(article =>
    [
      `"${article.data.id}"`,
      `"${article.data.num}"`,
      ...article.parents.map(parent => `"${parent.titre_ta || parent.titre}"`)
    ].join(";")
  );
  console.log(`"LEGI";"REF";"1";"2";"3";"4";"5";"6";"7";"8";"9"`);
  console.log(csv.join("\n"));
}
