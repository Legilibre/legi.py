const { cleanData } = require("./utils");

const makeArticle = data => ({
  type: "article",
  data: cleanData({
    ...data,
    titre_ta: `Article ${data.num}`
  })
});

module.exports = makeArticle;
