const { cleanData } = require("./utils");

const makeArticle = data => ({
  type: "article",
  data: cleanData({
    ...data,
    titre: data.num && `Article ${data.num}`
  })
});

module.exports = makeArticle;
