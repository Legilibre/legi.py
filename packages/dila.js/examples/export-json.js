const fs = require("fs");
const spinner = require("ora-promise");

const Legi = require("./src/Legi");

const { serialExec, range } = require("./src/utils");

const legi = new Legi();

// extract les datas d'un texte à une date YYYY-MM-DD avec spinner console
const extractDate = (id, date) => spinner(`${id}-${date}`, () => legi.getCode({ id, date }));

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

// ecrit les fichiers pour toutes les dates connues d'un code
const buildAllVersions = async id => buildDates(id, await getDates(id));

// pour un range donné
const buildYears = async id => buildDates(id, range(1977, 2019).map(y => `${y}-01-01`));

buildYears("LEGITEXT000006072050");
