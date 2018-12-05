const remove = require("unist-util-remove");
const map = require("unist-util-map");

// extract basic text structure
const getStructure = tree =>
  map(remove(tree, "article"), node => ({
    children: node.children,
    type: node.type,
    id: node.data.id,
    titre_ta: node.data.titre_ta
  }));

// se base sur un fichier extrait avec examples/export-json.js
if (require.main === module) {
  const tree = require("../2018-01-01.json");
  console.log(JSON.stringify(getStructure(tree), null, 2));
}
