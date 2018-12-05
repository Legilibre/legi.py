const getSommaire = require("./getSommaire");
const getArticleData = require("./getArticle");
const { cleanData } = require("./utils");

const getArticle = async (knex, id) => {
  const article = await getArticleData(knex, { id });
  if (!article) {
    return null;
  }
  const texteArticle = await getArticleData(knex, { cid: article.cid, id });
  return {
    type: "article",
    data: cleanData({
      titre: `Article ${article.num}`,
      ...texteArticle
    })
  };
};

const getSectionData = (knex, filters) =>
  filters.id &&
  knex
    //.debug()
    .clearSelect()
    .clearWhere()
    .clearOrder()
    .select()
    .from("sections")
    .where(filters)
    .first();

//
// generates a syntax-tree structure
// https://github.com/syntax-tree/unist
//
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
        const sectionData = await getSectionData(knex, { id: filters.id || filters.parent });
        return {
          type: "section",
          data: cleanData(sectionData) || {},
          children: children.filter(Boolean) // prevent nulls
        };
      })
      .catch(console.log)
  );
};

module.exports = getSection;
