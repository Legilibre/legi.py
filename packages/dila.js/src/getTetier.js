const { getStructure } = require("./getStructure");
const getTetierData = require("./getTetierData");
const { makeAst } = require("./utils");

const getTetier = (knex, { id, date }) =>
  getStructure({ knex, date, maxDepth: 0, parentId: id }).then(async rows => ({
    // make the final AST-like structure
    type: "tetier",
    // add root section data if needed
    data: await getTetierData(knex, { id }),
    children: makeAst(rows, id)
  }));

module.exports = getTetier;
