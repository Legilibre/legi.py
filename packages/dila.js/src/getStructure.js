const makeArticle = require("./makeArticle");
const makeSection = require("./makeSection");

// postgreSQL queries to get the full structure in a single-query

// basic SQL date/vigueur filters
const getSommaireFilters = (cid, date) =>
  `cid='${cid}' and sommaires.debut <= '${date}' and (sommaires.fin > '${date}' or sommaires.fin = '${date}' or sommaires.etat = 'VIGUEUR')`;

// add sections + articles basic data from the sommaires results
const getStructureSQL = ({
  cid,
  date,
  initialCondition = "sommaires.parent is null",
  maxDepth = 1
}) => `

${/* DECLARE RECURSIVE FUNCTION */ ""}
${/* get full structure in a one-shot flat array */ ""}

 WITH RECURSIVE hierarchie(element, depth) AS (
  SELECT sommaires.element, 0 as depth, sommaires.position, sommaires.etat, sommaires.num, sommaires.parent, sommaires.debut, sommaires.fin
    FROM sommaires
    WHERE ${getSommaireFilters(cid, date)}
    and ${initialCondition}
  UNION ALL
  SELECT DISTINCT sommaires.element, depth + 1 as depth, sommaires.position, sommaires.etat, sommaires.num, sommaires.parent, sommaires.debut, sommaires.fin
    FROM sommaires, hierarchie
    WHERE ${getSommaireFilters(cid, date)}
    and sommaires.parent = hierarchie.element
    ${maxDepth > 0 ? `and depth <= ${Math.max(0, maxDepth - 1)}` : ``}
 )

${/* map some data from previous recursive call */ ""}

SELECT  hierarchie.element as id, sections.parent, sections.titre_ta, hierarchie.position, hierarchie.etat, null as num
  from hierarchie
  left join sections on sections.id=hierarchie.element
  where LEFT(hierarchie.element, 8) = 'LEGISCTA'
union ALL(
SELECT  hierarchie.element as id, hierarchie.parent, CONCAT('Article ', COALESCE(hierarchie.num, articles.num)) as titre_ta, hierarchie.position, hierarchie.etat, COALESCE(hierarchie.num, articles.num, 'inconnu')
  from hierarchie
  left join articles on articles.id=hierarchie.element
  where LEFT(hierarchie.element, 8) = 'LEGIARTI'
  order by articles.id)

`;

// SQL where id IN (x, y, z) query
const getRowsIn = (knex, table, ids, key = "id") => knex.from(table).whereIn(key, ids);

const isSection = id => id.substring(0, 8) === "LEGISCTA";
const isArticle = id => id.substring(0, 8) === "LEGIARTI";

// get flat rows with the articles/sections for given section/date
const getRawStructure = async ({ knex, cid, section, date, maxDepth = 0 }) =>
  knex.raw(
    getStructureSQL({
      date,
      cid,
      maxDepth,
      initialCondition: section ? `sommaires.element='${section}'` : "sommaires.parent is null"
    })
  );
//.debug();

// build AST-like deep structure for a given node
// useful for full data dumps
const getStructure = async ({ knex, cid, section = undefined, date, maxDepth = 0 }) =>
  getRawStructure({ knex, cid, section, date, maxDepth }).then(async result => {
    // cache related data
    const allSections = await getRowsIn(
      knex,
      "sections",
      result.rows.filter(row => isSection(row.id)).map(row => row.id)
    );
    const allArticles = await getRowsIn(
      knex,
      "articles",
      result.rows.filter(row => isArticle(row.id)).map(row => row.id)
    );

    const getSection = row => allSections.find(section => section.id === row.id);
    const getArticle = row => allArticles.find(article => article.id === row.id);

    // enrich sommaire rows with related data (sections, articles)
    // add hierarchical data so we can build an AST later on
    const getRow = row => {
      if (row.id.substring(0, 8) === "LEGISCTA") {
        const section = getSection(row);
        return makeSection({
          ...section,
          position: row.position,
          parent: row.parent
        });
      } else if (row.id.substring(0, 8) === "LEGIARTI") {
        const article = getArticle(row);
        return makeArticle({
          ...article,
          position: row.position,
          parent: row.parent
        });
      }
    };
    return result.rows.map(getRow);
  });

module.exports = { getStructure, getRawStructure };
