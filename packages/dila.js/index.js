const fs = require("fs");
const spinner = require("ora-promise");

const Legi = require("./src/Legi");

//
// travail : LEGITEXT000006072050
// propriété intel. LEGITEXT000006069414
// ordonnance travail : JORFTEXT000000465978
// médailles : LEGITEXT000006070666
//

//const extractDateRaw = (id, date) => extract({ id, date });

// extract les datas d'un texte à une date YYYY-MM-DD avec spinner console
const extractDate = (id, date) => spinner(`${id}-${date}`, () => extract({ id, date }));

// ecrit les fichiers un à un pour une liste de dates donnée [YYYY-MM-DD]
const buildDates = (id, dates) =>
  serialExec(
    dates.map(date => () => {
      const dst = `./history/code-du-travail/${id}-${date}.json`;
      if (fs.existsSync(dst)) {
        spinner(`${id}-${date}: déjà existant`, () => Promise.resolve());
        return Promise.resolve();
      } else {
        return extractDate(id, date).then(content => {
          fs.writeFileSync(dst, JSON.stringify(content, null, 2));
          return content;
        });
      }
    })
  );

// ecrit les fichiers pour toutes les dates connues d'un code
const buildAllVersions = async id => buildDates(id, await getDates(id));

// renvoie le JSON pour un texte et une donnée
// extractDate("LEGITEXT000006072050", "2018-03-05")
//   .then(JSONlog)
//   .catch(console.log);

//LEGISCTA000006132321 Première partie : Les relations individuelles de travail
// getSections({ parent: "LEGISCTA000006132321", date: "2018-03-05" })
//   .then(JSONlog)
//   .catch(console.log);

//buildAllVersions("LEGITEXT000006070666").catch(console.log);

// class Legi {
//   constructor(dbPath = "./legi.sqlite") {
//     return extract(dbPath);
//   }
// }

module.exports = {};

/*{
  use: dbPath => {
    setDatabase(dbPath);
  },
  getCode: ({ id, date }) =>
    extract({
      id,
      date
    })
};*/

// getSections({ parent: "JORFTEXT000030126643", date: "2018-03-05" })
//   .then(console.log)
//   .catch(console.log);

//const sampleDates = ["2018-03-05"]; //Array.from({ length: 2019 - 1974 }, (k, v) => `${1974 + v}-01-01`);
//buildDates("LEGITEXT000006072050", sampleDates).catch(console.log);

// extractJORF("JORFTEXT000030126643")
//   .then(console.log)
//   .catch(console.log);

// getSections({ parent: "JORFTEXT000030126643", date: "2018-03-05" })
//   .then(JSONlog)
//   .catch(console.log);

// extractDate("LEGITEXT000006070666", "2018-03-05")
//   .then(JSONlog)
//   .catch(console.log);
