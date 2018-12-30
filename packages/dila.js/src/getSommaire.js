const { getRawStructure } = require("./getStructure");
const { makeAst, cleanData } = require("./utils");
const getCodeData = require("./getCodeData");

const isSection = id => id.substring(0, 8) === "LEGISCTA";

const getRow = row => ({
  type: "section",
  data: cleanData({
    id: row.id,
    titre_ta: row.titre_ta,
    position: row.position,
    parent: row.parent
  })
});

// return full structure without nested content and without articles. useful to build a navigation
const getSommaire = (knex, { cid, date }) =>
  getRawStructure({ knex, cid, date, maxDepth: 0 }).then(async result => ({
    // make the final AST-like structure
    type: "code",
    // add root section data if needed
    data: await getCodeData(knex, { cid }),
    children: makeAst(result.rows.filter(row => isSection(row.id)).map(getRow))
  }));

module.exports = getSommaire;
