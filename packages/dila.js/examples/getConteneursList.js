const dila = require("./dila");
const { JSONlog } = require("../src/utils");

// get code sommaire
dila
  .getConteneursList({ etat: ["VIGUEUR_ETEN"], nature: "TI" })
  .then(JSONlog)
  .catch(console.log)
  .then(dila.close);
