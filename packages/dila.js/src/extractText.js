const getSection = require("./getSection");
const getCodeDates = require("./getCodeDates");

const extractText = async (
  knex,
  { date = new Date().toLocaleDateString(), showVersions = false, ...filters }
) => {
  console.log("filters", filters)
  const textData = await knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select("cid", "titre", "titrefull", "date_publi")
    .from("textes_versions")
    .where({
      etat: "VIGUEUR"
    })
    .andWhere("date_debut", "<=", date)
    .andWhere("date_fin", ">", date)
    .andWhere(filters)
    .orderBy("date_publi", "desc")
    .first()
    .catch(console.log);

  // todo: codes metadatas: ajouter la liste des version dispos
  const tree = {
    type: "code",
    date,
    data: textData,
    children: (textData && [await getSection(knex, { cid: textData.cid, date })]) || []
  };

  if (showVersions) {
    tree.data.versions = await getCodeDates(knex, { id: textData.cid });
  }

  return tree;
};

module.exports = extractText;
