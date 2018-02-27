const fs = require("fs");

const db = "../legilibre/legi.py-docker/tarballs/legilibre.sqlite";
/*
todo : handle dates

articles :
  id:
  section:
  num:
  etat:
  date_debut:

*/

const remark = require("remark");
const strip = require("remark-strip-html");

const stripHtml = content =>
  remark()
    .use(strip)
    .process(content);

// const knex = require("knex")({
//   client: "sqlite3",
//   connection: {
//     filename: db
//   }
// });

const knex = require("knex")({
  client: "pg",
  connection: "postgresql://postgres:test@127.0.0.1:5433/legi",
  searchPath: ["knex", "public"]
});

const getCode = titre =>
  knex
    .select()
    .from("textes_versions")
    .where("titre", titre)
    .first();

const getCodeDuTravail = () => getCode("Code du travail");

const getCodePI = () => getCode("Code de la propriété intellectuelle");

const getLinks = () =>
  getCodeDuTravail().then(r =>
    knex
      .select()
      .from("liens")
      .where("dst_cid", r.cid)
      .limit(10)
  );

const links = () =>
  getLinks()
    .then(links => {
      links.forEach(link => {
        const id = link.dst_id;
        if (link.dst_id.match(/^LEGITEXT/)) {
          knex
            .select()
            .from("textes_versions")
            .where("id", id)
            .first()
            .then(texte => {
              if (!texte) {
                throw new Error("no textes_versions " + id);
              }
              //console.log("textes_versions", texte.id);
            })
            .catch(e => {
              console.log("ERR: cant find " + id);
            });
        } else if (id.match(/^LEGIARTI/)) {
          knex
            .select()
            .from("articles")
            .where("id", id)
            .first()
            .then(article => {
              if (!article) {
                throw new Error("no article " + id);
              }
              //console.log("article", article.id);
            })
            .catch(e => {
              console.log("ERR: cant find " + id);
            });
        }
      });
    })
    .catch(console.log);

const getTablesNames = async () =>
  knex("sqlite_master")
    .where("type", "table")
    .then(r => r.map(x => x.name));

const getColumns = async table => knex.table(table).columnInfo();

const dumpStructure = async () => {
  const tables = await getTablesNames();
  tables.forEach(async table => {
    const columns = await getColumns(table);
    console.log(`

## ${table}

name | type | description
-----|:----:|-------------`);
    Object.keys(columns).forEach(column => {
      console.log(`${column} | ${columns[column].type} | `);
    });
  });
  console.log("tables", tables);
};

const TABLES_MAP = { ARTI: "articles", SCTA: "sections" };

const getTableNameFromLegiId = id => {
  const type = id.substring(4, 8);
  const table = TABLES_MAP[type];
  return table;
};

// serial-chain promises
const serial = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c.then(cur => [...res, cur])),
    Promise.resolve([])
  );

const getEntryDetails = async entry => {
  const table = getTableNameFromLegiId(entry.element);
  return await knex
    .table(table)
    .where("id", entry.element)
    .first();
};

// recursive
const getEntryStructure = async ({ cid, entry }) => {
  const table = getTableNameFromLegiId(entry.element);

  const details = await getEntryDetails(entry);
  //console.log("d", d);
  const entryData = {
    ...details,
    sections: []
  };

  if (table === "sections" && entry.element !== cid) {
    const childEntries = await knex.table("sommaires").where({
      cid,
      parent: entry.element
    });
    entryData.sections = await serial(
      childEntries.map(entry2 =>
        getEntryStructure({
          entry: entry2,
          cid
        })
      )
    );
  }

  return entryData;
};

const getStructure = async cid => {
  const firstVersion = await knex
    .table("textes_versions")
    .where("cid", cid)
    .first();
  if (!firstVersion) {
    return [];
  }
  const sommaire = await knex
    .table("sommaires")
    .where({ cid, _source: `struct/${firstVersion.id}` })
    .orderBy("position", "ASC");
  return await serial(
    sommaire.map(x =>
      getEntryStructure({
        cid: cid,
        entry: x
      })
    )
  );
};

const test = async () => {
  const cdt = await getCodePI();
  const structure = await getStructure(cdt.cid);
};

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
    return cleanStr(article.bloc_textuel);
  }
  return "";
};

const cleanStr = async str => {
  const breaked = str
    .replace(/<p>/g, "\n")
    .replace(/<br\s?\/?>/g, "\n\n")
    .replace(/<\/p>/g, "");
  return await stripHtml(breaked).then(x => x.toString().trim());
};

const getTitreSection = id =>
  knex
    .select("titre_ta")
    .from("sections")
    .where("id", id)
    .first()
    .then(r => r.titre_ta);

const getArticle = id =>
  knex
    .select("id", "num")
    .from("articles")
    .where("id", id)
    .first();

const getContent = ({ heading, titre, content }) => `
${heading} ${titre}

${content}
`;

const getSectionsText = async ({ debut, fin, cid, parent = false, depth = 1 }) => {
  const sections = await getSections({
    debut,
    fin,
    cid,
    parent
  }).catch(console.log);
  const heading = Array.from({ length: depth })
    .fill("#")
    .join("");
  return Promise.all(
    sections.map(async section => {
      const typeSection = section.element.substring(4, 8);
      if (typeSection === "SCTA") {
        const titre_ta = await getTitreSection(section.element);
        const content = await getSectionsText({
          debut,
          fin,
          cid,
          parent: section.element,
          depth: depth + 1
        });
        return getContent({ heading, titre: titre_ta, content: content.join("\n") });
      } else if (typeSection === "ARTI") {
        const article = await getArticle(section.element);
        const texteArticle = await getTexteArticle({ cid, id: article.id });
        return getContent({
          heading,
          titre: `Article ${article.num}`,
          content: texteArticle
        });
      } else {
        return "?";
      }
    })
  );
  //.then(arr => arr.reduce((a, c) => [...a, ...c], []));
};

const getSections = ({ debut, fin, cid, parent = false }) => {
  const sections = knex
    .select("*")
    .table("sommaires")
    .where("cid", cid)
    .andWhere("debut", "<=", debut)
    .andWhere(function() {
      return this.where("fin", ">=", fin)
        .orWhere("fin", "2999-01-01")
        .orWhere("etat", "VIGUEUR");
    })
    .andWhere(function() {
      if (parent) {
        return this.where("parent", parent);
      } else {
        return this.where("parent", null).orWhere("parent", "");
      }
    })
    .orderBy("position");

  return sections;
};

const getVersionsDates = async id => {
  const versions = await knex
    .select("debut", "fin")
    .debug()
    .table("sommaires")
    .where("cid", id)
    .orderBy("debut");

  const debuts = new Set(versions.map(x => x.debut));
  const fins = new Set(versions.map(x => x.fin));
  const versionsDates = Array.from(debuts.add(fins));
  versionsDates.sort();
  return versionsDates;
};

const pAll = all => Promise.all(all);

const timeout = delay => x => new Promise((resolve, reject) => setTimeout(() => resolve(x), delay));

const getTexteByDate = (id, date) =>
  getSectionsText({
    debut: date,
    fin: date,
    cid: id
  }).then(arr => arr.join("\n\n"));

const getTexteHistory = async id => {
  let texte = await knex
    .table("textes_versions")
    .where("id", id)
    .first();
  if (!texte) {
    texte = await knex
      .table("textes_versions")
      .where("cid", id)
      .first();
  }

  const texteId = texte.cid;

  const versionsDates = await getVersionsDates(texteId);

  const allVersions = await versionsDates.map((debut, i) => async () => {
    if (i >= versionsDates.length - 2) {
      return Promise.resolve();
    }
    const fin = versionsDates[i + 1];
    const path = `./history/${fin}.md`;

    if (!fs.existsSync(path)) {
      const text = await getSectionsText({
        debut,
        fin,
        cid: texteId,
        parent: false
      }).then(arr => arr.join("\n\n"));
      fs.writeFileSync(`./history/${fin}.md`, text);
      return Promise.resolve(text);
    }
  });

  //serial
  serial(allVersions)
    //.then(console.log)
    .catch(console.log);
  //)

  /*
    promises.then((res, i) => res.slice(0, -1))
    .then(versions => {
      const byDate = versions.reduce(
        (a, c, i) => ({
          ...a,
          ...(c && { [versionsDates[i]]: c })
        }),
        {}
      );
      Object.keys(byDate).forEach(date => {
        console.log("byDate", date);
        fs.writeFileSync(`./history/${date}.md`, byDate[date]);
      });
      // const fs =require('fs');
      // fs.writeFileSync(`./${}`);
      return byDate;
    });
    */
};

// travail : LEGITEXT000006072050
// propriété intel. LEGITEXT000006069414

getTexteByDate("LEGITEXT000006072050", "25/12/2017")
  .then(console.log)
  .catch(console.log)
  .then(() => {
    knex.destroy();
  });
//getTexteHistory("LEGITEXT000006069414")
//.then(x => console.log(x)) //(JSON.stringify(x, null, 2)))
//.catch(console.log);

//dumpStructure();

//test();
