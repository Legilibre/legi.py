const Legi = require("./src");

const { serialExec, JSONlog } = require("./src/utils");

const legi = new Legi("legi1.sqlite");

const markdown = require("./src/markdown");
const html = require("./src/html");

// liste des codes disponibles
const codesDispo = () => legi.getCodesList();

// code du travail au format unist (~3min)
const codeDuTravail = () => legi.getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" });

// liste des versions du code du travail (dates)
const versionsDuCodeDuTravail = () => legi.getCodeDates("LEGITEXT000006072050");

// générer toutes les version d'un texte au format unist (très long)
const getAllVersions = async id => {
  const dates = await legi.getCodeDates(id);
  return serialExec(dates.map(date => () => legi.getCode({ id, date })));
};

// ordonnance au format unist
const getOrdonnance12Mars2007 = () => legi.getJORF("JORFTEXT000000465978");

// section d'un texte au format unist
const getPremierePartieCodeDuTravail = () =>
  legi.getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" });

// conversion d'un tree unist en markdown
const toMarkdown = () => legi.getCode("LEGITEXT000006069414").then(markdown);

// conversion d'un tree unist en html
const toHtml = () => legi.getCode("LEGITEXT000006069414").then(html);
