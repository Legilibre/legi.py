const fs = require("fs");
const visit = require("unist-util-visit");

const Legi = require("../src/Legi");

const legi = new Legi();
const { range, JSONread } = require("../src/utils");

/*
JORFTEXT000036386252 -> versions.cid=JORFTEXT000036386252 & sommaires.cid="JORFTEXT000036386252" VIGUEUR, > num
  JORFARTI000036386255 -> LEGIARTI000036534472
    LEGIARTI000036247089 -> liens : src_id=LEGIARTI000036534472 -> dst_id="LEGIARTI000036247089" -> LEGIARTI000036247089
  JORFARTI000036386257 -> LEGIARTI000036532190
  JORFARTI000036386258 -> LEGIARTI000036532191

article dans CDT -> LEGIARTI000036247490

*/
// const getPath = (id = "LEGITEXT000006072050", date = "2018-01-01") =>
//   `./history/code-du-travail/${id}-${date}.json`;

// const filterAllBy = (tree, predicate) => {
//   const results = [];
//   visit(tree, visitor);
//   function visitor(node) {
//     if (predicate(node)) results.push(node);
//   }
//   return results;
// };

// // volumétrie par an
// const getYearStats = year => {
//   const content = JSONread(getPath("LEGITEXT000006072050", `${year}-01-01`));
//   return {
//     year,
//     sections: filterAllBy(content, n => n.type === "section").length,
//     articles: filterAllBy(content, n => n.type === "article").length
//   };
// };

const CODE = "LEGITEXT000006072050"; // code du travail

const test = async () => {
  const results = await legi.getCodeVersions(CODE);
  //console.log("results", results.length);
  //console.log("result[0]", results[0]);
  const item = results.filter(r => r.debut === "2017-12-23");

  //articles.id = LEGIARTI000036247490
  console.log("item", item);
  // legi.knex
  //   .distinct("element")
  //   .select()
  //   .from("sommaires")
  //   .where({ debut: "2018-01-13", cid: "LEGITEXT000006072050", etat: "VIGUEUR" })
  //   .then(console.log);

  // legi.knex
  //   .select()
  //   .from("textes_versions")
  //   .where({ cid: "JORFTEXT000036386252" })
  //   .then(console.log);
  //results[.forEach(result => {
  // legi.knex
  //   .select("element")
  //   .from("sommaires")
  //   .then(console.log);
  //})
  //console.log(JSON.stringify(results, null, 2));

  legi.close();
};

test().catch(console.log);

//console.log(JSON.stringify(results, null, 2));
