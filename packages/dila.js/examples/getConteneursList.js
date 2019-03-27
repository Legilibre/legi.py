const legi = require("./legi");
const { JSONlog } = require("../src/utils");

// get code sommaire
legi
  .getConteneursList({ etat: ["VIGUEUR_ETEN"], nature: "TI" })
  .then(JSONlog)
  .catch(console.log)
  .then(legi.close);
