const { cleanData } = require("./utils");

const makeSection = data => ({
  type: "section",
  data: cleanData(data)
});

module.exports = makeSection;
