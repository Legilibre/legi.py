const { getStructure } = require("./getStructure");
const getConteneurData = require("./getConteneurData");
const { makeAst } = require("./utils");

const getConteneur = (knex, { id, date }) =>
  getStructure({ knex, date, maxDepth: 0, parentId: id }).then(async rows => ({
    // make the final AST-like structure
    type: "conteneur",
    // add root section data if needed
    data: await getConteneurData(knex, { id }),
    children: makeAst(rows, id)
  }));

module.exports = getConteneur;
