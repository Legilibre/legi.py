//
// i have a DB full of small content that i need to arrange hierachically; i was wondering if "converting" the data to a tree
//

const knexConfig = require("./knexfile");
const boxen = require("boxen");

const knex = require("knex")(knexConfig[process.env.NODE_ENV] || knexConfig.postgres);

const serial = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c.then(cur => [...res, cur])),
    Promise.resolve([])
  );

const getTexteArticle = async ({ id, cid }) => {
  const article = await knex
    .select("bloc_textuel")
    .table("articles")
    .where({
      id,
      cid
    })
    .first();
  if (article && article.bloc_textuel) {
    return article.bloc_textuel;
  }
  return "";
};

const getArticle = id =>
  knex
    .select("id", "num")
    .from("articles")
    .where("id", id)
    .first();

const cleanUpTitreSection = t =>
  t
    .replace(/&#13;/g, "")
    .replace(/\n/g, " ")
    .trim();

const getTitreSection = id =>
  knex
    .select("titre_ta")
    .from("sections")
    .where("id", id)
    .first()
    .then(r => cleanUpTitreSection(r.titre_ta));

const getSommaire = filters => {
  const sommaireFilters = {
    ...filters
  };
  delete sommaireFilters.fin; // ?????

  return (
    knex
      .table("sommaires")
      //.debug()
      .where(sommaireFilters)
      .andWhere("debut", "<=", filters.fin)
      .andWhere(function() {
        return this.where("fin", ">=", filters.fin)
          .orWhere("fin", "2999-01-01")
          .orWhere("etat", "VIGUEUR");
      })
      .orderBy("position")
      .catch(console.log)
  );
};

const getSections = async ({ ...filters }) => {
  if (!filters.parent) {
    filters.parent = null;
  }
  const sommaire = await getSommaire(filters);
  // if (filters.parent === "LEGISCTA000018535721") {
  //   console.log("sommaire", sommaire);
  // }
  return (
    sommaire &&
    Promise.all(
      sommaire.map(async section => {
        if (section.element.match(/^LEGISCTA/)) {
          return {
            title: await getTitreSection(section.element),
            children: await getSections({ ...filters, parent: section.element })
          };
        } else if (section.element.match(/^LEGIARTI/)) {
          const article = await getArticle(section.element);
          const texteArticle = await getTexteArticle({ cid: filters.cid, id: article.id });
          return {
            title: `Article ${article.num}`,
            html: texteArticle
          };
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
      if (!n.title.match(/^Article.*/)) console.log(r("  ", d), n.title);
      logSections(n, d + 1);
    });
};

const extract = async ({ id, fin = new Date().toLocaleDateString() }) => {
  const text = await knex
    .select("cid", "titre", "titrefull", "date_publi")
    .table("textes_versions")
    .where({
      id: id,
      etat: "VIGUEUR"
    })
    .andWhere("date_debut", "<=", fin)
    .andWhere("date_fin", ">=", fin)
    .orderBy("date_publi", "desc")
    .first()
    .catch(console.log);

  const title = `${text.titre} : ${fin}`;

  console.log(boxen(title, { padding: 1 }));

  const tree = {
    children: await getSections({ cid: text.cid, fin })
  };

  logSections(tree);
};

// travail : LEGITEXT000006072050
// propriété intel. LEGITEXT000006069414
// ordonnance travail : JORFTEXT000000465978

extract({ id: "LEGITEXT000006072050" }).then(() => knex.destroy());

//select * from sommaires where parent="LEGISCTA000018535721" and (etat="VIGUEUR" or fin>=date() or fin="2999-01-01") and debut <= date()

// getSections({ cid: "LEGITEXT000006072050", fin: "2018-03-05", parent: "LEGISCTA000018535721" })
//   .then(console.log)
//   .catch(console.log);
