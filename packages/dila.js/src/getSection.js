const getSommaire = require("./getSommaire");
const getArticleData = require("./getArticle");

const getArticle = async (knex, id) => {
  const article = await getArticleData(knex, { id });
  const texteArticle = await getArticleData(knex, { cid: article.cid, id });
  return {
    type: "article",
    data: {
      titre: `Article ${article.num}`,
      ...texteArticle
    }
  };
};

const getSectionData = (knex, filters) =>
  knex
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select()
    .from("sections")
    .where(filters)
    .first();

// generates a syntax-tree structure
// https://github.com/syntax-tree/unist
const getSection = async (knex, filters) => {
  if (!filters.parent) {
    filters.parent = null;
  }
  const sommaire = await getSommaire(knex, {
    ...filters,
    id: undefined,
    parent: filters.id || filters.parent
  });
  if (!sommaire) {
    return;
  }
  if (!sommaire.map) {
    return sommaire;
  }
  return (
    sommaire &&
    Promise.all(
      sommaire.map(async section => {
        if (section.element.match(/^LEGISCTA/)) {
          return await getSection(knex, { ...filters, id: undefined, parent: section.element });
        } else if (section.element.match(/^LEGIARTI/)) {
          return await getArticle(knex, section.element);
        } else {
          return {
            id: section.element
          };
          console.log("invalid section ?", section);
        }
      })
    )
      .then(async children => {
        const sectionData = await getSectionData(knex, { id: filters.parent || filters.parent });
        return {
          type: "section",
          data: sectionData || {},
          children
        };
      })
      .catch(console.log)
  );
};

module.exports = getSection;
