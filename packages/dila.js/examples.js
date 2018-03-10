const Legi = require("./src");

const { serialExec, JSONlog } = require("./src/utils");

const legi = new Legi("legi1.sqlite");

// liste des codes disponibles
// legi
//   .getCodesList()
//   .then(JSONlog)
//   .catch(console.log);

// const texte1 = legi
//   .getCode({ id: "LEGITEXT000006072050", date: "2012-03-05" })
//   .then(JSONlog)
//   .catch(console.log);

// // get all available dates for a given text
// const texte2 = legi
//   .getCodeDates("LEGITEXT000006072050")
//   .then(JSONlog)
//   .catch(console.log);

// // generate all version of a given text
// const getAllVersions = async id => {
//   const dates = await legi.getCodeDates(id);
//   return serialExec(dates.map(date => () => legi.getCode({ id, date })));
// };

// getAllVersions("LEGITEXT000006070666")
//   .then(JSONlog)
//   .catch(console.log);

legi
  .getJORF("JORFTEXT000000465978")
  .then(JSONlog)
  .catch(console.log);
