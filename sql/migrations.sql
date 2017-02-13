This is not meant to be run directly.

-- migration #1
CREATE TABLE textes_versions_brutes
( id char(20) unique not null
, bits int not null
, nature text
, titre text
, titrefull text
, autorite text
, num text
, date_texte day
, dossier text not null
, cid char(20) not null
, mtime int not null
);
CREATE VIEW textes_versions_brutes_view AS
    SELECT a.dossier, a.cid, a.id,
           (CASE WHEN b.bits & 1 > 0 THEN b.nature ELSE a.nature END) AS nature,
           (CASE WHEN b.bits & 2 > 0 THEN b.titre ELSE a.titre END) AS titre,
           (CASE WHEN b.bits & 4 > 0 THEN b.titrefull ELSE a.titrefull END) AS titrefull,
           (CASE WHEN b.bits & 8 > 0 THEN b.autorite ELSE a.autorite END) AS autorite,
           (CASE WHEN b.bits & 16 > 0 THEN b.num ELSE a.num END) AS num,
           (CASE WHEN b.bits & 32 > 0 THEN b.date_texte ELSE a.date_texte END) AS date_texte
      FROM textes_versions a
 LEFT JOIN textes_versions_brutes b
        ON b.id = a.id AND b.cid = a.cid AND b.dossier = a.dossier AND b.mtime = a.mtime;
