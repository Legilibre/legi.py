const { getStructure } = require("./getStructure");
const getCodeData = require("./getCodeData");
const { makeAst } = require("./utils");

const getCode = (knex, { cid, date }) =>
  getStructure({ knex, cid, date, maxDepth: 0 }).then(async rows => ({
    // make the final AST-like structure
    type: "code",
    // add root section data if needed
    data: await getCodeData(knex, { cid }),
    children: makeAst(rows)
  }));

module.exports = getCode;
