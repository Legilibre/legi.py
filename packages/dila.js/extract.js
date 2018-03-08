const memoize = require("fast-memoize");

//
// i have a DB full of small content that i need to arrange hierachically; i was wondering if "converting" the data to a tree
//
//const normalizeWhitespace = require("normalize-html-whitespace");
const knexConfig = require("./knexfile");

const knex = require("knex")(knexConfig);

const serial = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c.then(cur => [...res, cur])),
    Promise.resolve([])
  );

const serialExec = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c().then(cur => [...res, cur])),
    Promise.resolve([])
  );

// const getTexteArticle = async ({ id, cid }) => {
//   const article = await knex
//     .select("bloc_textuel")
//     .table("articles")
//     .where({
//       id,
//       cid
//     })
//     .first();
//   // todo: cleanup
//   if (article && article.bloc_textuel) {
//     return article.bloc_textuel;
//   }
//   return "";
// };

const getArticle = memoize(filters =>
  knex
    .select("*")
    .from("articles")
    .where(filters)
    .first()
);

const getArticleById = memoize(id => getArticle({ id }));

// const cleanUpTitreSection = t =>
//   t
//     .replace(/&#13;/g, "")
//     .replace(/\n/g, " ")
//     .trim();

const getSection = memoize(id =>
  knex
    .select("*")
    .from("sections")
    .where("id", id)
    .first()
);

// const getTitreSection = id =>
//   knex
//     .select("titre_ta")
//     .from("sections")
//     .where("id", id)
//     .first()
//     .then(r => cleanUpTitreSection(r.titre_ta));

const getSommaire = memoize(filters => {
  const sommaireFilters = {
    ...filters
  };
  delete sommaireFilters.date; // ?????

  return (
    knex
      .table("sommaires")
      //.debug()
      .where(sommaireFilters)
      .andWhere("debut", "<=", filters.date)
      .andWhere(function() {
        return this.where("fin", ">=", filters.date)
          .orWhere("fin", "2999-01-01")
          .orWhere("etat", "VIGUEUR");
      })
      .orderBy("position")
      .catch(console.log)
  );
});

//replace(/<br\s?\/?>/g, "\n");

// generates a syntax-tree structure
// https://github.com/syntax-tree/unist
const getSections = async ({ ...filters }) => {
  if (!filters.parent) {
    filters.parent = null;
  }
  const sommaire = await getSommaire(filters);
  return (
    sommaire &&
    Promise.all(
      sommaire.map(async section => {
        //   console.log("section");
        if (section.element.match(/^LEGISCTA/)) {
          const sectionData = await getSection(section.element);
          return {
            type: "section",
            data: sectionData,
            children: await getSections({ ...filters, parent: section.element })
          };
        } else if (section.element.match(/^LEGIARTI/)) {
          const article = await getArticleById(section.element);
          const texteArticle = await getArticle({ cid: article.cid, id: article.id });
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

const r = (s, times = 5) =>
  Array.from({ length: times })
    .fill(s)
    .join("");

const logSections = (node, d = 0) => {
  node.children &&
    node.children.forEach(n => {
      if (n.titre.match(/^Article.*/)) {
        console.log(r("  ", d), n.titre);
        n.bloc_textuel && console.log(r("  ", d + 1), n.bloc_textuel, "\n\n");
      } else {
        console.log(r("  ", d), n.titre);
        logSections(n, d + 1);
      }
    });
};

const extract = async ({ id, date = new Date().toLocaleDateString() }) => {
  const text = await knex
    .select("cid", "titre", "titrefull", "date_publi")
    .table("textes_versions")
    .where({
      id: id,
      etat: "VIGUEUR"
    })
    .andWhere("date_debut", "<=", date)
    .andWhere("date_fin", ">=", date)
    .orderBy("date_publi", "desc")
    .first()
    .catch(console.log);

  const tree = {
    type: "code",
    id,
    date,
    children: (text && (await getSections({ cid: text.cid, date }))) || []
  };

  //logSections(tree);
  //  knex.destroy();
  return tree;
};

const getDates = async id => {
  const versions = await knex
    .select("debut", "fin")
    //.debug()
    .table("sommaires")
    .where("cid", id)
    .orderBy("debut");

  const allVersions = Array.from(versions.reduce((a, c) => a.add(c.debut).add(c.fin), new Set()));

  allVersions.sort();

  return allVersions;
};

module.exports = {
  extract,
  getDates,
  serial,
  serialExec,
  getSections
};
// travail : LEGITEXT000006072050
// propriété intel. LEGITEXT000006069414
// ordonnance travail : JORFTEXT000000465978

//extract({ id: "LEGITEXT000006072050" }).then(() => knex.destroy());

//select * from sommaires where parent="LEGISCTA000018535721" and (etat="VIGUEUR" or fin>=date() or fin="2999-01-01") and debut <= date()

// getSections({ cid: "LEGITEXT000006072050", fin: "2018-03-05", parent: "LEGISCTA000018535721" })
//   .then(console.log)
//   .catch(console.log);
