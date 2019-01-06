const makeArticle = require("./makeArticle");
const getArticleData = require("./getArticleData");

const getLiens = (knex, { id }) =>
  knex
    .raw(
      `
      select src_id, dst_cid, dst_id, articles.cid as article_cid,
            (case when length(dst_titre) = 0 then
              case when length(textes_versions.num) = 0 then
                textes_versions.titre
              else
                CONCAT(textes_versions.titre, ' - Article ', articles.num)
              end
            else
              dst_titre
            end) as dst_titre,
            liens.dst_titre as dst_titre1, typelien,textes_versions.titre
            from liens
            left join articles on articles.id = liens.src_id
            left join textes_versions on textes_versions.cid=articles.cid
            where src_id = '${id}' or (dst_id = '${id}')
      `
    )
    .then(result => result.rows);

const getArticle = async (knex, { id }) => {
  const article = await getArticleData(knex, { id });
  const liens = await getLiens(knex, { id });
  if (!article) {
    return null;
  }
  return makeArticle({
    ...article,
    liens
  });
};

module.exports = getArticle;
