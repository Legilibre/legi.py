const Legi = require("legi");

const legi = new Legi();

// liste des codes disponibles
legi.getCodesList();

// code du travail (~3min)
legi.getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" });

// liste des versions du code du travail
legi.getCodeVersions("LEGITEXT000006072050");

// ordonnance
legi.getJORF("JORFTEXT000000465978");

// section d'un texte
legi.getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" });

// conversion en markdown
const markdown = require("legi/src/markdown");
legi.getCode("LEGITEXT000006069414").then(markdown);

// conversion en html
const html = require("legi/src/html");
legi.getCode("LEGITEXT000006069414").then(html);
