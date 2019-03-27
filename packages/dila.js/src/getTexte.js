const { getStructure } = require("./getStructure");
const getTexteData = require("./getTexteData");
const { makeAst } = require("./utils");

const getTexte = (knex, { id, date }) =>
  getStructure({ knex, parentId: id, date, maxDepth: 0 }).then(async rows => ({
    // make the final AST-like structure
    type: "texte",
    // add root section data if needed
    data: await getTexteData(knex, { id }),
    children: makeAst(rows, id)
  }));

module.exports = getTexte;
