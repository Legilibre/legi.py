const { getStructure } = require("./getStructure");
const getSectionData = require("./getSectionData");
const { makeAst } = require("./utils");

const getSection = async (knex, { cid, id = null, date, maxDepth = 2 }) => {
  if (id && !cid) {
    // detect cid
    cid = (await knex
      .select("cid")
      .from("sommaires")
      .where({ element: id })
      .first()).cid;
  }
  return getStructure({ knex, cid, date, section: id, maxDepth }).then(async rows => ({
    // make the final AST-like structure
    type: "section",
    data: await getSectionData(knex, { id }),
    children: makeAst(rows, id)
  }));
};

module.exports = getSection;
