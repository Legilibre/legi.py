const memoize = require("fast-memoize");
const knexRequire = require("knex");

// default sqlite config
const getKnexConfig = dbPath => ({
  client: "sqlite3",
  useNullAsDefault: true,
  connection: {
    filename: dbPath
  },
  pool: {}
});

const legi = dbPath => {
  const knex = knexRequire(getKnexConfig(dbPath)); //.debug();

  const getArticle = memoize(filters =>
    knex
      .select("*")
      .from("articles")
      .where(filters)
      .first()
  );

  const getArticleById = memoize(id => getArticle({ id }));

  const getSectionData = memoize(id =>
    knex
      .select("*")
      .from("sections")
      .where("id", id)
      .first()
  );

  const getSommaire = memoize(filters => {
    const sommaireFilters = {
      ...filters
    };
    delete sommaireFilters.date; // not a valid sql field

    return (
      knex
        .table("sommaires")
        //.debug()
        .where(sommaireFilters)
        .andWhere("debut", "<=", filters.date)
        .andWhere(function() {
          return this.where("fin", ">", filters.date)
            .orWhere("fin", "2999-01-01")
            .orWhere("etat", "VIGUEUR");
        })
        .orderBy("position")
        .catch(console.log)
    );
  });

  const getCodesList = () => knex.table("textes_versions").where({ nature: "CODE" });

  const extractVersion = async ({ date = new Date().toLocaleDateString(), ...filters }) => {
    const text = await knex
      .select("cid", "titre", "titrefull", "date_publi")
      .table("textes_versions")
      .where({
        etat: "VIGUEUR"
      })
      .andWhere(filters)
      .andWhere("date_debut", "<=", date)
      .andWhere("date_fin", ">", date)
      .orderBy("date_publi", "desc")
      .first()
      .catch(console.log);

    // todo: codes metadatas: ajouter la liste des version dispos
    const tree = {
      type: "code",
      date,
      data: text,
      children: (text && (await getSection({ cid: text.cid, date }))) || []
    };

    return tree;
  };

  const getCodeDates = async id => {
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

  const getJORF = async id => {
    const version = await knex
      .table("textes_versions")
      .where({ cid: id })
      .first();
    const articles = await knex
      .table("articles")
      .where({ cid: id })
      .orderBy("num");

    const children = articles.map(a => ({
      id: a.id,
      type: "article",
      data: a,
      children: []
    }));

    return {
      id,
      type: "texte",
      data: version,
      children
    };
  };

  // generates a syntax-tree structure
  // https://github.com/syntax-tree/unist
  const getSection = async ({ ...filters }) => {
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
            const sectionData = await getSectionData(section.element);
            return {
              type: "section",
              data: sectionData,
              children: await getSection({ ...filters, parent: section.element })
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

  const getCodeId = code => {
    if (code.match(/^LEGITEXT/)) {
      return code;
    }
    // todo: fuse
    return CODES[code];
  };

  const getCodeParams = params => {
    const isSingleString = params.length === 1 && typeof params[0] === "string";
    return isSingleString ? { id: params[0] } : params[0];
  };

  const close = () => {
    console.log("destroy");
    knex.destroy();
  };

  return {
    getCode: (...args) => extractVersion(getCodeParams(args)),
    getCodeDates,
    getCodesList,
    getJORF,
    getSection,
    close,
    knex
  };
};

class Legi {
  constructor(dbPath = "./legi.sqlite") {
    return legi(dbPath);
  }
}

module.exports = Legi;
