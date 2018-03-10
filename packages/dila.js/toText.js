const find = require("unist-util-find");
const map = require("unist-util-map");
const toHTML = require("hast-util-to-html");

// only log sections
const logSection = (node, depth = 0) => {
  if (depth > 0 && node.type !== "section") {
    return;
  }
  const tab = Array.from({ length: depth * 2 })
    .fill("  ")
    .join("");
  const titre = node.data && (node.data.titre_ta || node.data.titre).trim();
  titre && console.log(tab, titre);
  node.children && node.children.forEach(child => logSection(child, depth + 1));
};

const data = require("./history/code-du-travail/LEGITEXT000006072050-2018-03-05.json");

//logSection(data);

const getSection = (tree, id) => find(tree, node => node.type === "section" && node.data.id === id);

const section = getSection(data, "LEGISCTA000006132321");

const actual = map(section, function(node) {
  if (node.type === "section") {
    return {
      ...node,
      type: "element",
      tagName: "p",
      properties: {
        style: "font-weight: bold"
      },
      children: [
        {
          type: "text",
          value: node.data.titre_ta
        }
      ]
    };
  } else if (node.type === "article") {
    return {
      ...node,
      type: "element",
      tagName: "p",
      properties: {
        style: "font-weight: bold"
      },
      children: [
        {
          type: "text",
          value: node.data.titre
        }
      ]
    };
  }
  // no change
  return node;
});

//console.log(JSON.stringify(actual, null, 2));

console.log(toHTML(actual));
