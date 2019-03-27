const { cleanData } = require("./utils");

const makeTetier = data => ({
  type: "tetier",
  data: cleanData(data)
});

module.exports = makeTetier;
