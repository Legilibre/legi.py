const { cleanData } = require("./utils");

const makeArticle = data => ({
  type: "article",
  data: cleanData({
    ...data,
    titre_ta: data.num && `Article ${data.num}`
  })
});

module.exports = makeArticle;
