const getSommaire = require("./getSommaire");
const getArticle = require("./getArticle");

const getSectionData = (knex, filters) =>
  knex
    .select("*")
    .from("sections")
    .where(filters)
    .first();

// generates a syntax-tree structure
// https://github.com/syntax-tree/unist
const getSection = async (knex, { filters }) => {
  if (!filters.parent) {
    filters.parent = null;
  }
  const sommaire = await getSommaire(knex, { filters: filters });
  return (
    sommaire &&
    Promise.all(
      sommaire.map(async section => {
        //   console.log("section");
        if (section.element.match(/^LEGISCTA/)) {
          const sectionData = await getSectionData(knex, { id: section.element });
          return {
            type: "section",
            data: sectionData,
            children: await getSection(knex, { filters: { ...filters, parent: section.element } })
          };
        } else if (section.element.match(/^LEGIARTI/)) {
          const article = await getArticle(knex, { id: section.element });
          const texteArticle = await getArticle(knex, { cid: article.cid, id: article.id });
          const data = {
            titre: `Article ${article.num}`,
            ...texteArticle
          };
          return {
            type: "article",
            data
          };
        } else {
          console.log("invalid section ?", section);
        }
      })
    )
  );
};

module.exports = getSection;
