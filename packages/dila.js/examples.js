const Legi = require("./src");

const { serialExec, JSONlog } = require("./src/utils");

const legi = new Legi("legi1.sqlite");

const markdown = require("./src/markdown");
const html = require("./src/html");

// liste des codes disponibles
// legi
//   .getCodesList()
//   .then(JSONlog)

// const texte1 = legi
//   .getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" })
//   .then(JSONlog)

// // get all available dates for a given text
// const texte2 = legi
//   .getCodeDates("LEGITEXT000006072050")
//   .then(JSONlog)

// // generate all version of a given text
// const getAllVersions = async id => {
//   const dates = await legi.getCodeDates(id);
//   return serialExec(dates.map(date => () => legi.getCode({ id, date })));
// };

// getAllVersions("LEGITEXT000006070666")
//   .then(JSONlog)

// legi
//   .getJORF("JORFTEXT000000465978")
//   .then(JSONlog)

//
// legi
//   .getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" })
//   .then(JSONlog)

// conversion en markdown
// legi.getCode("LEGITEXT000006069414").then(node => {
//   markdown(node)
//     .then(console.log)
// })
// conversion en html
legi.getCode("LEGITEXT000006069414").then(node => {
  html(node).then(console.log);
});

// toHTML(node)
//   .then(console.log)
//   .catch(e => console.log("e", e));
//});
// .then(nodeToMdast)
// .then(stringifyMdast)
// //.then(stringify)
// .then(console.log)
// .catch(e => console.log("e", e));
/*
  stringify : compter les mots par année
*/
