const getSection = require("./getSection");
const getCodeDates = require("./getCodeDates");
const { cleanData } = require("./utils");

//
// extrait l'arbre d'un texte à une date donnée
// utilise legi.textes_versions pour récupérer la version en date
// puis construit les sections et le contenu
//

const extractText = async (
  knex,
  { date = new Date().toLocaleDateString(), showVersions = false, ...filters }
) => {
  const textData = await knex
    //.debug()
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
    type: "text",
    date,
    data: cleanData(textData),
    children: (textData && (await getSection(knex, { cid: textData.cid, date })).children) || []
  };

  if (showVersions) {
    tree.data.versions = await getCodeDates(knex, { id: textData.cid });
  }

  return tree;
};

module.exports = extractText;
