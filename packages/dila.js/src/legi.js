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

  const getCodesList = () => knex.table("textes_versions").where({ nature: "CODE" });

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

  // const getCodeId = code => {
  //   if (code.match(/^LEGITEXT/)) {
  //     return code;
  //   }
  //   // todo: fuse
  //   return CODES[code];
  // };

  // const getCodeParams = params => {
  //   const isSingleString = params.length === 1 && typeof params[0] === "string";
  //   return isSingleString ? { id: params[0] } : params[0];
  // };

  const close = () => {
    console.log("destroy");
    knex.destroy();
  };

  return {
    getCode: params => require("./getCode")(knex, params),
    //=> extractVersion(getCodeParams(args)),
    getCodeDates: ({ id }) => require("./getCodeDates")(knex, { id }),
    getCodesList,
    getJORF,
    getSection: filters => require("./getSection")(knex, { filters }),
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
