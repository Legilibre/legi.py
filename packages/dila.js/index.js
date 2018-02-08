const db = "../legilibre/legi.py-docker/tarballs/legilibre.sqlite";
/*

articles :
  id:
  section:
  num:
  etat:
  date_debut:

*/

const knex = require("knex")({
  client: "sqlite3",
  connection: {
    filename: db
  }
});

const getCodeDuTravail = () =>
  knex
    .select()
    .from("textes_versions")
    .where("titre", "Code du travail")
    .first();

const getCodePI = () =>
  knex
    .select()
    .from("textes_versions")
    .where("titre", "Code de la propriété intellectuelle")
    .first();

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
              console.log("textes_versions", texte.id);
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
              console.log("article", article.id);
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
  promises.reduce((chain, c) => chain.then(res => c.then(cur => [...res, cur])), Promise.resolve([]));

// recursive
const getEntryStructure = async ({ cid, entry }) => {
  const table = getTableNameFromLegiId(entry.element);

  const entryData = {
    ...entry,
    sections: []
  };
  //console.log("entryData", entryData);
  if (table === "sections" && entry.element !== cid) {
    entryData.sections = await serial(
      (await knex.table("sommaires").where({
        cid,
        parent: entry.element
      })).map(entry2 =>
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
  const versions = await knex.table("textes_versions").where("cid", cid);
  const firstVersion = versions[0];
  const sommaire = await knex
    .table("sommaires")
    .where({ cid: cid, _source: `struct/${firstVersion.id}` })
    .orderBy("position", "ASC");
  console.log("sommaire", sommaire);
  const structure = await serial(
    sommaire.map(x =>
      getEntryStructure({
        cid: cid,
        entry: x
      })
    )
  );

  return structure;
};

const test = async () => {
  const cdt = await getCodePI();
  const structure = await getStructure(cdt.cid);
  console.log("structure", JSON.stringify(structure, null, 2));
};

//dumpStructure();

test();
