const routes = require("express").Router();
const find = require("unist-util-find");
const parents = require("unist-util-parents");

const getParentSections = require("../../getParentSections");

// extract basic text structure
const getSection = (tree, id) => {
  const section = find(
    parents(tree),
    node => node.type === "section" && node.data.id === id
  );
  if (section.parent) {
    section.parents = getParentSections(section);
  }
  return section;
};

routes.get("/texte/:texte/section/:section", async (req, res) => {
  const data = require(`../../legi.js/codes/${req.params.texte}.json`);
  res.json(getSection(data, req.params.section));
});

module.exports = routes;
