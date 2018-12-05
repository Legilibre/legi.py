const fs = require("fs");
const visit = require("unist-util-visit");
const spinner = require("ora-promise");

const { serialExec, range, JSONlog } = require("../src/utils");

const Legi = require("../src/Legi");

const legi = new Legi({
  client: "sqlite3",
  connection: {
    filename: "legilibre.sqlite"
  }
});

// extract les datas d'un texte à une date YYYY-MM-DD avec spinner console
const extractDate = (id, date) => spinner(`${id}-${date}`, () => legi.getCode({ id, date }));

//const legi = new Legi();

const CODE = "LEGITEXT000006072050"; // code du travail

// ecrit les fichiers un à un pour une liste de dates donnée [YYYY-MM-DD]
const buildDates = (id, dates) =>
  serialExec(
    dates.map(date => () => {
      const dst = `./history/${id}/${date}.json`;
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

// // pour un range donné
// const buildYears = async id => buildDates(id, range(2010, 2019).map(y => `${y}-01-01`));

// // extrait le code du travail sur X années
// buildYears("LEGITEXT000006072050").then(() => legi.close());

const test = async () => {
  return legi
    .getCodeVersions(CODE)

    .then(versions =>
      versions
        .map(({ debut }) => debut)
        .filter(date => new Date(date).getFullYear() >= 2015)
        .map(date => date.substring(0, 10))
    )
    .then(dates => buildDates(CODE, dates));
};

test()
  .then(console.log)
  .catch(console.log)
  .then(legi.close);
