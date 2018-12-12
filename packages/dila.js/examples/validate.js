const fs = require("fs");
const spinner = require("ora-promise");

const Legi = require("../src/Legi");

const { serialExec, range, JSONlog } = require("../src/utils");

//const legi = new Legi();

const legi = new Legi({
  client: "sqlite3",
  connection: {
    filename: "legilibre.sqlite"
  }
});

legi
  .getSection({ id: "LEGISCTA000006195589", date: "2018-12-06" })
  .then(sec => {
    console.log(JSON.stringify(sec, null, 2));
  })
  .then(legi.close);

// // extract les datas d'un texte à une date YYYY-MM-DD avec spinner console
// const extractDate = (id, date) => spinner(`${id}-${date}`, () => legi.getCode({ id, date }));

// // ecrit les fichiers un à un pour une liste de dates donnée [YYYY-MM-DD]
// const buildDates = (id, dates) =>
//   serialExec(
//     dates.map(date => () => {
//       const dst = `./history/${id}/${date}.json`;
//       if (fs.existsSync(dst)) {
//         spinner(`${id}-${date}: déjà existant`, () => Promise.resolve());
//         return Promise.resolve();
//       } else {
//         return extractDate(id, date).then(content => {
//           fs.writeFileSync(dst, JSON.stringify(content, null, 2));
//           return content;
//         });
//       }
//     })
//   );

// // pour un range donné
// const buildYears = async id => buildDates(id, range(2010, 2019).map(y => `${y}-01-01`));

// // extrait le code du travail sur X années
// //buildYears("LEGITEXT000006072050").then(() => legi.close());

// // extrait code des médaills
// extractDate("LEGITEXT000006072050", "2018-12-01")
//   .then(JSONlog)
//   .catch(console.log)
//   .then(legi.close);
