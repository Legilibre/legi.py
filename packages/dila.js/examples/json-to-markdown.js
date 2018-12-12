//const { selectAll } = require("unist-util-select");

const markdown = require("../src/markdown");

// const getParentSections = (node, chain = []) => {
//   if (node.parent && node.parent.type === "section") {
//     return getParentSections(
//       node.parent,
//       (chain = [
//         {
//           titre_ta: node.parent.data.titre_ta,
//           id: node.parent.data.id
//         },
//         ...chain
//       ])
//     );
//   }
//   return chain;
// };

// use file built with examples/export-json.js
if (require.main === module) {
  const json = require("../2018-12-06-2.json");
  markdown(json)
    .then(console.log)
    .catch(console.log);
}
