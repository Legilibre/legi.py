const { cleanData } = require("./utils");

const makeTexte = data => ({
  type: "texte",
  data: cleanData(data)
});

module.exports = makeTexte;
